"""
U/N Algebra: Uncertainty/Nominal Algebra
Complementary dual to N/U Algebra

Author: Eric D. Martin
Version: 1.0 Alpha
License: CC BY 4.0

Core library for U/N algebraic operations.
"""

import math
from typing import Tuple, Union, Optional, List
from dataclasses import dataclass
import numpy as np


@dataclass
class NUPair:
    """Standard N/U pair (nominal, uncertainty)."""
    n: float  # Nominal value
    u: float  # Uncertainty (must be ≥ 0)
    
    def __post_init__(self):
        self.u = max(0.0, self.u)  # Enforce non-negativity
    
    def __repr__(self):
        return f"NU({self.n:.6f}, {self.u:.6f})"
    
    def add(self, other: 'NUPair') -> 'NUPair':
        """N/U addition: (n₁, u₁) ⊕ (n₂, u₂) = (n₁+n₂, u₁+u₂)"""
        return NUPair(self.n + other.n, self.u + other.u)
    
    def multiply(self, other: 'NUPair', lam: float = 1.0) -> 'NUPair':
        """N/U multiplication: (n₁, u₁) ⊗ (n₂, u₂) = (n₁n₂, |n₁|u₂ + |n₂|u₁ + λu₁u₂)"""
        n_prod = self.n * other.n
        u_prod = abs(self.n) * other.u + abs(other.n) * self.u + lam * self.u * other.u
        return NUPair(n_prod, u_prod)
    
    def scale(self, a: float) -> 'NUPair':
        """Scalar multiplication: a ⊙ (n, u) = (an, |a|u)"""
        return NUPair(a * self.n, abs(a) * self.u)
    
    def invariant_M(self) -> float:
        """Uncertainty invariant: M(n, u) = |n| + u"""
        return abs(self.n) + self.u
    
    def bounds(self) -> Tuple[float, float]:
        """Return [n-u, n+u]"""
        return (self.n - self.u, self.n + self.u)


@dataclass
class UNAlgebra:
    """
    U/N Algebra element: ((n_a, u_t), (n_m, u_m))
    - (n_a, u_t): Actual/Tolerance (epistemic tier)
    - (n_m, u_m): Measured/Measurement (observation tier)
    """
    actual_pair: NUPair    # (n_a, u_t)
    measured_pair: NUPair  # (n_m, u_m)
    
    def __post_init__(self):
        """Ensure all uncertainties are non-negative."""
        self.actual_pair.u = max(0.0, self.actual_pair.u)
        self.measured_pair.u = max(0.0, self.measured_pair.u)
    
    def __repr__(self):
        return f"UN(({self.actual_pair.n:.4f}, {self.actual_pair.u:.4f}), ({self.measured_pair.n:.4f}, {self.measured_pair.u:.4f}))"
    
    # ===== CORE OPERATIONS =====
    
    def add(self, other: 'UNAlgebra') -> 'UNAlgebra':
        """
        U/N Addition (Definition 3):
        UN₁ ⊕ UN₂ = ((n_a1 + n_a2, u_t1 + u_t2), (n_m1 + n_m2, u_m1 + u_m2))
        """
        actual_result = self.actual_pair.add(other.actual_pair)
        measured_result = self.measured_pair.add(other.measured_pair)
        return UNAlgebra(actual_result, measured_result)
    
    def multiply(self, other: 'UNAlgebra') -> 'UNAlgebra':
        """
        U/N Multiplication (Definition 4):
        Multiply each nested pair, including quadratic uncertainty terms.

        Result:
        - n_a_result = n_a1 * n_a2
        - u_t_result = |n_a1|u_t2 + |n_a2|u_t1 + cross-terms + quadratic terms
        - n_m_result = n_m1 * n_m2
        - u_m_result = |n_m1|u_m2 + |n_m2|u_m1 + u_m1*u_m2
        """
        # Actual multiplication (linear terms)
        n_a_result = self.actual_pair.n * other.actual_pair.n
        u_t_linear = (abs(self.actual_pair.n) * other.actual_pair.u +
                      abs(other.actual_pair.n) * self.actual_pair.u)

        # Measured multiplication (linear terms)
        n_m_result = self.measured_pair.n * other.measured_pair.n
        u_m_linear = (abs(self.measured_pair.n) * other.measured_pair.u +
                      abs(other.measured_pair.n) * self.measured_pair.u)

        # Cross-terms (|n_m| with u_t, |n_a| with u_m)
        cross_terms = (abs(self.measured_pair.n) * other.actual_pair.u +
                       abs(other.measured_pair.n) * self.actual_pair.u)

        # Quadratic uncertainty terms (for conservativity)
        quad_u_t = self.actual_pair.u * other.actual_pair.u
        quad_u_m = self.measured_pair.u * other.measured_pair.u
        quad_mixed = (self.actual_pair.u * other.measured_pair.u +
                      self.measured_pair.u * other.actual_pair.u)

        u_t_result = u_t_linear + cross_terms + quad_u_t + quad_mixed
        u_m_result = u_m_linear + quad_u_m

        actual_result = NUPair(n_a_result, u_t_result)
        measured_result = NUPair(n_m_result, u_m_result)
        
        return UNAlgebra(actual_result, measured_result)
    
    def scale(self, a: float) -> 'UNAlgebra':
        """
        Scalar Multiplication (Definition 5):
        a ⊙ UN = ((a·n_a, |a|u_t), (a·n_m, |a|u_m))
        """
        actual_result = self.actual_pair.scale(a)
        measured_result = self.measured_pair.scale(a)
        return UNAlgebra(actual_result, measured_result)
    
    def subtract(self, other: 'UNAlgebra') -> 'UNAlgebra':
        """
        U/N Subtraction (Definition 6):
        UN₁ ⊖ UN₂ = UN₁ ⊕ ((-1) ⊙ UN₂)
        """
        negated = other.scale(-1.0)
        return self.add(negated)
    
    # ===== SPECIAL OPERATORS =====
    
    def catch(self) -> 'UNAlgebra':
        """
        Catch Operator (Definition 8):
        Collapse actual tier to zero, absorb all into measurement uncertainty.
        C_U/N(UN) = ((0, 0), (n_m, |n_m - n_a| + u_t + u_m))
        """
        n_a, u_t = self.actual_pair.n, self.actual_pair.u
        n_m, u_m = self.measured_pair.n, self.measured_pair.u
        
        collapsed_u_m = abs(n_m - n_a) + u_t + u_m
        
        actual_result = NUPair(0.0, 0.0)
        measured_result = NUPair(n_m, collapsed_u_m)
        
        return UNAlgebra(actual_result, measured_result)
    
    def flip(self) -> 'UNAlgebra':
        """
        Flip Operator (Definition 9):
        Swap actual/tolerance with measured/precision.
        B_U/N(UN) = ((n_m, u_m), (n_a, u_t))
        """
        return UNAlgebra(self.measured_pair, self.actual_pair)
    
    def flip_twice(self) -> 'UNAlgebra':
        """Verify involution property: B(B(UN)) = UN"""
        return self.flip().flip()
    
    # ===== INVARIANTS & PROPERTIES =====
    
    def invariant_M(self) -> float:
        """
        U/N Invariant (Definition 7):
        M(UN) = |n_a| + u_t + |n_m| + u_m
        Total epistemic budget across both tiers.
        """
        return (abs(self.actual_pair.n) + self.actual_pair.u + 
                abs(self.measured_pair.n) + self.measured_pair.u)
    
    def triangle_inequality_check(self) -> bool:
        """
        Check triangle inequality (Axiom 2):
        |n_m - n_a| ≤ u_t + u_m
        """
        n_a, u_t = self.actual_pair.n, self.actual_pair.u
        n_m, u_m = self.measured_pair.n, self.measured_pair.u
        
        diff = abs(n_m - n_a)
        bound = u_t + u_m
        
        return diff <= bound + 1e-10  # Small epsilon for floating-point tolerance
    
    def triangle_inequality_gap(self) -> float:
        """Return how much room we have in triangle inequality."""
        n_a, u_t = self.actual_pair.n, self.actual_pair.u
        n_m, u_m = self.measured_pair.n, self.measured_pair.u
        
        diff = abs(n_m - n_a)
        bound = u_t + u_m
        
        return bound - diff
    
    # ===== PROJECTION TO N/U =====
    
    def project_to_NU(self, n_a_known: bool = True) -> NUPair:
        """
        Project to N/U (Definition 2):
        
        Case A (n_a known): π(UN) = (n_m, |n_m - n_a| + u_m)
        Case B (n_a unknown): π(UN) = (n_m, u_t + u_m)
        """
        n_a, u_t = self.actual_pair.n, self.actual_pair.u
        n_m, u_m = self.measured_pair.n, self.measured_pair.u
        
        if n_a_known:
            return NUPair(n_m, abs(n_m - n_a) + u_m)
        else:
            return NUPair(n_m, u_t + u_m)
    
    # ===== BOUNDS & INTERVALS =====
    
    def actual_bounds(self) -> Tuple[float, float]:
        """Return [n_a - u_t, n_a + u_t]"""
        return self.actual_pair.bounds()
    
    def measured_bounds(self) -> Tuple[float, float]:
        """Return [n_m - u_m, n_m + u_m]"""
        return self.measured_pair.bounds()
    
    def combined_bounds(self) -> Tuple[float, float]:
        """Return overall bounds accounting for both tiers."""
        n_a, u_t = self.actual_pair.n, self.actual_pair.u
        n_m, u_m = self.measured_pair.n, self.measured_pair.u
        
        # Worst-case: actual could be far from measured
        lower = min(n_a - u_t, n_m - u_m)
        upper = max(n_a + u_t, n_m + u_m)
        
        return (lower, upper)
    
    # ===== VALIDATION & DIAGNOSTICS =====
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'n_a': self.actual_pair.n,
            'u_t': self.actual_pair.u,
            'n_m': self.measured_pair.n,
            'u_m': self.measured_pair.u,
            'invariant_M': self.invariant_M(),
            'triangle_valid': self.triangle_inequality_check(),
        }


# ===== UTILITY FUNCTIONS =====

def create_UN(n_a: float, u_t: float, n_m: float, u_m: float) -> UNAlgebra:
    """Convenience constructor for U/N values."""
    return UNAlgebra(NUPair(n_a, u_t), NUPair(n_m, u_m))


def conservativity_check(un1: UNAlgebra, un2: UNAlgebra, op_name: str = 'add') -> bool:
    """
    Verify conservativity (Theorem 9):
    u_proj(UN₁ ○ UN₂) ≥ (π(UN₁) ○_N/U π(UN₂)).u

    Note: Uses n_a_known=False projection to avoid cancelation issues
    with the absolute difference |n_m - n_a|.
    """
    if op_name == 'add':
        result = un1.add(un2)
    elif op_name == 'multiply':
        result = un1.multiply(un2)
    else:
        raise ValueError(f"Unknown operation: {op_name}")

    # Project result and inputs (using unknown n_a case for conservativity)
    u_proj_result = result.project_to_NU(n_a_known=False).u

    # Direct N/U operations
    pi_un1 = un1.project_to_NU(n_a_known=False)
    pi_un2 = un2.project_to_NU(n_a_known=False)

    if op_name == 'add':
        direct_result_u = pi_un1.add(pi_un2).u
    else:
        direct_result_u = pi_un1.multiply(pi_un2).u

    # Check: projected should be ≥ direct
    return u_proj_result >= direct_result_u - 1e-10


def verify_associativity(un1: UNAlgebra, un2: UNAlgebra, un3: UNAlgebra, 
                         op_name: str = 'add') -> Tuple[bool, float]:
    """
    Verify associativity (Theorem 6):
    (UN₁ ○ UN₂) ○ UN₃ = UN₁ ○ (UN₂ ○ UN₃)
    
    Returns (is_associative, max_difference)
    """
    if op_name == 'add':
        left = un1.add(un2).add(un3)
        right = un1.add(un2.add(un3))
    elif op_name == 'multiply':
        left = un1.multiply(un2).multiply(un3)
        right = un1.multiply(un2.multiply(un3))
    else:
        raise ValueError(f"Unknown operation: {op_name}")
    
    # Compare all components
    max_diff = max(
        abs(left.actual_pair.n - right.actual_pair.n),
        abs(left.actual_pair.u - right.actual_pair.u),
        abs(left.measured_pair.n - right.measured_pair.n),
        abs(left.measured_pair.u - right.measured_pair.u),
    )
    
    is_associative = max_diff < 1e-9
    
    return is_associative, max_diff


# ===== COSMOLOGICAL APPLICATION: HUBBLE CONSTANT EXAMPLE =====

def hubble_UN_merge(early_H0: UNAlgebra, late_H0: UNAlgebra, 
                    tensor_distance: float = 1.0) -> UNAlgebra:
    """
    Merge Hubble measurements using U/N algebra with tensor distance.
    
    Args:
        early_H0: U/N representation of early-universe measurement
        late_H0: U/N representation of late-universe measurement
        tensor_distance: Epistemic distance Δ_T between frameworks
    
    Returns:
        Merged U/N value with expanded uncertainty
    """
    # Base merge: average nominals, combine uncertainties
    n_a_merged = (early_H0.actual_pair.n + late_H0.actual_pair.n) / 2
    u_t_base = (early_H0.actual_pair.u + late_H0.actual_pair.u) / 2
    
    n_m_merged = (early_H0.measured_pair.n + late_H0.measured_pair.n) / 2
    u_m_base = (early_H0.measured_pair.u + late_H0.measured_pair.u) / 2
    
    # Expand tolerance by epistemic distance
    disagreement = abs(early_H0.measured_pair.n - late_H0.measured_pair.n)
    u_t_expanded = u_t_base + (disagreement / 2) * tensor_distance
    
    return UNAlgebra(
        NUPair(n_a_merged, u_t_expanded),
        NUPair(n_m_merged, u_m_base)
    )


if __name__ == "__main__":
    # Quick validation example
    print("=== U/N Algebra: Python Implementation ===\n")
    
    # Create two U/N values
    un1 = create_UN(n_a=10.0, u_t=0.5, n_m=10.1, u_m=0.2)
    un2 = create_UN(n_a=20.0, u_t=0.3, n_m=19.9, u_m=0.1)
    
    print(f"UN₁: {un1}")
    print(f"UN₂: {un2}")
    print(f"Triangle valid (UN₁): {un1.triangle_inequality_check()}")
    print(f"Triangle valid (UN₂): {un2.triangle_inequality_check()}\n")
    
    # Addition
    un_sum = un1.add(un2)
    print(f"UN₁ ⊕ UN₂: {un_sum}")
    print(f"Triangle valid: {un_sum.triangle_inequality_check()}")
    print(f"Invariant M: {un_sum.invariant_M():.6f}\n")
    
    # Multiplication
    un_prod = un1.multiply(un2)
    print(f"UN₁ ⊗ UN₂: {un_prod}")
    print(f"Triangle valid: {un_prod.triangle_inequality_check()}\n")
    
    # Projection
    proj = un1.project_to_NU(n_a_known=True)
    print(f"π(UN₁) [n_a known]: {proj}")
    
    # Operators
    caught = un1.catch()
    print(f"\nC_U/N(UN₁): {caught}")
    
    flipped = un1.flip()
    print(f"B_U/N(UN₁): {flipped}")
    
    flipped_twice = un1.flip_twice()
    print(f"B(B(UN₁)): {flipped_twice}")
    print(f"Involution preserved: {flipped_twice.to_dict() == un1.to_dict()}\n")
    
    # Associativity check
    un3 = create_UN(n_a=5.0, u_t=0.2, n_m=5.05, u_m=0.15)
    is_assoc, max_diff = verify_associativity(un1, un2, un3, op_name='add')
    print(f"Addition associativity: {is_assoc} (max diff: {max_diff:.2e})")
    
    is_assoc, max_diff = verify_associativity(un1, un2, un3, op_name='multiply')
    print(f"Multiplication associativity: {is_assoc} (max diff: {max_diff:.2e})\n")
    
    # Conservativity
    cons_add = conservativity_check(un1, un2, 'add')
    cons_mul = conservativity_check(un1, un2, 'multiply')
    print(f"Conservativity (addition): {cons_add}")
    print(f"Conservativity (multiplication): {cons_mul}")
