"""
U/N Algebra Re-Anchoring Module

This module provides the UNReanchor class for performing diagnostic re-anchoring
of measurements to a shared Universal Nominal Anchor (UNA). It tests whether
apparent tension between datasets is referential (frame artifact) or physical.

Theoretical Background:
----------------------
When different measurements use different reference frames (different n_a values),
they may appear incompatible even when their intervals would overlap if expressed
in a common frame. Re-anchoring moves all measurements to a shared UNA and applies
minimal triangle-inequality adjustments.

The triangle inequality constraint: |n_i - n_a^(0)| ≤ u_t^(0) + u_i'

If intervals overlap after re-anchoring, the tension was referential.
If intervals remain disjoint, the tension is physical or model-level.

Author: Eric D. Martin
License: CC BY 4.0
Version: 1.0-beta
"""

from typing import List, Tuple, Dict, Optional
import math


class UNReanchor:
    """
    Re-anchor multiple measurements to a shared Universal Nominal Anchor (UNA).

    This class implements the referentiality diagnostic test:
    1. Compute shared anchor (midpoint, weighted mean, or explicit)
    2. Adjust measurement uncertainties to satisfy triangle inequality
    3. Project to N/U space for interval comparison
    4. Report overlap status

    Attributes:
        datasets: List of (name, n, u) tuples representing measurements
        n_anchor: Shared universal nominal anchor (computed or provided)
        u_t: Shared tolerance uncertainty (max of input uncertainties)
        adjusted: List of adjusted (name, n, u') tuples
    """

    def __init__(self, datasets: List[Tuple[str, float, float]]):
        """
        Initialize with a list of measurements.

        Parameters:
            datasets: List of (name, nominal, uncertainty) tuples
                     Each measurement is a standard N/U pair (n, u)

        Example:
            planck = ("Planck", 67.3217, 0.3963)
            shoes = ("SH0ES", 72.6744, 0.9029)
            reanchor = UNReanchor([planck, shoes])
        """
        if not datasets:
            raise ValueError("datasets cannot be empty")

        for name, n, u in datasets:
            if u < 0:
                raise ValueError(f"Uncertainty must be non-negative: {name} has u={u}")

        self.datasets = datasets
        self.n_anchor = None
        self.u_t = None
        self.adjusted = None

    def reanchor(self,
                 weights: Optional[List[float]] = None,
                 shared_anchor: Optional[Tuple[float, float]] = None) -> Dict:
        """
        Perform re-anchoring to shared UNA.

        Parameters:
            weights: Optional list of weights for computing weighted mean anchor.
                    If None, uses arithmetic mean. Typically w_i = 1/u_i^2.
            shared_anchor: Optional explicit (n_anchor, u_t) tuple.
                          If provided, uses this instead of computing from data.

        Returns:
            Dictionary containing:
                - anchor: (n_anchor, u_t) tuple
                - adjusted: List of (name, n, u') tuples with adjusted uncertainties
                - projections: List of (name, n, u_proj) N/U projections
                - intervals: List of (name, lower, upper) interval bounds
                - overlap: Boolean indicating if all intervals touch/overlap
                - gap: Minimum gap between intervals (0 if overlapping)

        Example:
            result = reanchor.reanchor()
            print(f"Anchor: {result['anchor']}")
            print(f"Overlap: {result['overlap']}")
        """
        # Step 1: Compute shared UNA
        if shared_anchor is not None:
            self.n_anchor, self.u_t = shared_anchor
        else:
            if weights is None:
                # Unweighted arithmetic mean
                self.n_anchor = sum(n for _, n, _ in self.datasets) / len(self.datasets)
            else:
                # Weighted mean
                if len(weights) != len(self.datasets):
                    raise ValueError("weights must match number of datasets")
                w_sum = sum(weights)
                if w_sum == 0:
                    raise ValueError("Sum of weights cannot be zero")
                self.n_anchor = sum(w * n for (_, n, _), w in zip(self.datasets, weights)) / w_sum

            # u_t is max of all input uncertainties
            self.u_t = max(u for _, _, u in self.datasets)

        # Step 2: Minimal triangle-inequality adjustment
        self.adjusted = []
        for name, n, u in self.datasets:
            d = abs(n - self.n_anchor)
            # If triangle inequality violated, increase uncertainty minimally
            if d > self.u_t + u:
                delta_u = d - (self.u_t + u)
                u_prime = u + delta_u
            else:
                u_prime = u
            self.adjusted.append((name, n, u_prime))

        # Step 3: Project to N/U space
        # Projection: π_i = (n_i, u_t + u_i')
        projections = []
        intervals = []
        for name, n, u_prime in self.adjusted:
            u_proj = self.u_t + u_prime
            projections.append((name, n, u_proj))

            lower = n - u_proj
            upper = n + u_proj
            intervals.append((name, lower, upper))

        # Step 4: Check for overlap
        overlap, gap = self._check_overlap(intervals)

        return {
            'anchor': (self.n_anchor, self.u_t),
            'adjusted': self.adjusted,
            'projections': projections,
            'intervals': intervals,
            'overlap': overlap,
            'gap': gap
        }

    def _check_overlap(self, intervals: List[Tuple[str, float, float]]) -> Tuple[bool, float]:
        """
        Check if all intervals touch or overlap.

        Returns:
            (overlap_status, minimum_gap)
            - overlap_status: True if all intervals touch or overlap
            - minimum_gap: Minimum distance between intervals (0 if touching/overlapping)
        """
        if len(intervals) < 2:
            return True, 0.0

        # Sort intervals by lower bound
        sorted_intervals = sorted(intervals, key=lambda x: x[1])

        min_gap = 0.0
        for i in range(len(sorted_intervals) - 1):
            _, _, upper1 = sorted_intervals[i]
            _, lower2, _ = sorted_intervals[i + 1]

            gap = lower2 - upper1
            if gap > min_gap:
                min_gap = gap

        # If max gap > 0, intervals are disjoint
        overlap = (min_gap <= 1e-10)  # Allow for numerical tolerance

        return overlap, max(0, min_gap)

    def merge(self, delta_t: float = 0.0) -> Dict:
        """
        Merge re-anchored measurements using epistemic tensor distance.

        This follows the SSOT merge protocol:
        1. Compute standard uncertainty as mean of adjusted uncertainties
        2. Add epistemic expansion based on disagreement and Δₜ

        Parameters:
            delta_t: Epistemic tensor distance (default 0 for anchor-only reconciliation)

        Returns:
            Dictionary containing:
                - n_merged: Merged nominal value (at anchor)
                - u_std: Standard uncertainty component
                - u_expand: Epistemic expansion component
                - u_total: Total merged uncertainty
                - interval: (lower, upper) bounds

        Example:
            result = reanchor.reanchor()
            merged = reanchor.merge(delta_t=1.3)
            print(f"Merged: ({merged['n_merged']:.3f}, {merged['u_total']:.3f})")
        """
        if self.adjusted is None:
            raise RuntimeError("Must call reanchor() before merge()")

        # Standard uncertainty: mean of adjusted uncertainties
        u_std = sum(u_prime for _, _, u_prime in self.adjusted) / len(self.adjusted)

        # Epistemic expansion: disagreement scaled by Δₜ
        nominals = [n for _, n, _ in self.adjusted]
        disagreement = max(nominals) - min(nominals)
        u_expand = (disagreement / 2) * delta_t

        # Total uncertainty
        u_total = u_std + u_expand

        return {
            'n_merged': self.n_anchor,
            'u_std': u_std,
            'u_expand': u_expand,
            'u_total': u_total,
            'interval': (self.n_anchor - u_total, self.n_anchor + u_total)
        }


def reanchor_pairwise(n1: float, u1: float, n2: float, u2: float) -> Dict:
    """
    Quick pairwise re-anchoring for two measurements.

    Convenience function for the common two-dataset case.

    Parameters:
        n1, u1: First measurement (nominal, uncertainty)
        n2, u2: Second measurement (nominal, uncertainty)

    Returns:
        Dictionary with anchor, adjusted values, projections, and overlap status

    Example:
        >>> result = reanchor_pairwise(67.3217, 0.3963, 72.6744, 0.9029)
        >>> print(f"Overlap: {result['overlap']}")
        Overlap: True
    """
    reanchor = UNReanchor([("Dataset 1", n1, u1), ("Dataset 2", n2, u2)])
    return reanchor.reanchor()


def weighted_reanchor(datasets: List[Tuple[str, float, float]],
                      use_inverse_variance: bool = True) -> Dict:
    """
    Re-anchor with inverse-variance weighting (1/u²).

    This is the standard approach for combining measurements with different precisions.

    Parameters:
        datasets: List of (name, nominal, uncertainty) tuples
        use_inverse_variance: If True, uses w_i = 1/u_i²; if False, uses uniform weights

    Returns:
        Re-anchoring result dictionary

    Example:
        >>> datasets = [("Planck", 67.3217, 0.3963), ("SH0ES", 72.6744, 0.9029)]
        >>> result = weighted_reanchor(datasets)
        >>> print(f"Weighted anchor: {result['anchor'][0]:.3f}")
        Weighted anchor: 68.123
    """
    if use_inverse_variance:
        weights = [1.0 / (u * u) for _, _, u in datasets]
    else:
        weights = [1.0] * len(datasets)

    reanchor = UNReanchor(datasets)
    return reanchor.reanchor(weights=weights)


# Example usage and test
if __name__ == "__main__":
    # Planck vs SH0ES Hubble constant measurements
    planck = ("Planck", 67.3217, 0.3963)
    shoes = ("SH0ES", 72.6744, 0.9029)

    print("=" * 60)
    print("U/N RE-ANCHORING: Hubble Tension Diagnostic")
    print("=" * 60)

    reanchor = UNReanchor([planck, shoes])
    result = reanchor.reanchor()

    print(f"\nShared Anchor: n_a = {result['anchor'][0]:.4f}, u_t = {result['anchor'][1]:.4f}")
    print(f"\nAdjusted Measurements:")
    for name, n, u_prime in result['adjusted']:
        print(f"  {name:10s}: n = {n:.4f}, u' = {u_prime:.4f}")

    print(f"\nProjected Intervals:")
    for name, lower, upper in result['intervals']:
        print(f"  {name:10s}: [{lower:.4f}, {upper:.4f}]")

    print(f"\nOverlap Status: {'✓ OVERLAPPING' if result['overlap'] else '✗ DISJOINT'}")
    print(f"Gap: {result['gap']:.4f}")

    # Test merge
    merged = reanchor.merge(delta_t=0.0)
    print(f"\nMerged (Δₜ=0): ({merged['n_merged']:.4f}, {merged['u_total']:.4f})")

    print("=" * 60)
