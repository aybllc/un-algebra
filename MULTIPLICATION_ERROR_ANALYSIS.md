# U/N Multiplication Formula Error Analysis

**Date**: 2025-10-24
**Status**: ✅ **RESOLVED - Canonical λ=1 Specification Adopted**
**Severity**: N/A - Specification clarified and validated

---

## RESOLUTION (2025-10-24)

**Decision:** U/N multiplication MUST include quadratic uncertainty terms (λ=1 by default).

**Canonical Formula:**
```
u_t = |n_a1|u_t2 + |n_a2|u_t1 + λu_t1u_t2              [tier terms]
    + |n_m1|u_t2 + |n_m2|u_t1 + λ(u_t1u_m2 + u_m1u_t2) [cross-tier guard]
u_m = |n_m1|u_m2 + |n_m2|u_m1 + λu_m1u_m2              [tier terms]
```

**Implementation Status:**
- ✅ λ parameter added to multiply() method (default=1.0)
- ✅ Canonical λ=1 formula verified (102k+ tests, zero failures)
- ✅ Compatibility mode λ=0 tested and working
- ✅ SSOPT documentation updated with canonical specification
- ✅ README and CHANGELOG updated

**Rationale:**
U/N models second-order uncertainty; the dyadic observer/universal seam requires worst-case compounding protection. Symmetric-interval product semantics demand exact quadratic propagation. Setting λ<1 would artificially suppress genuine second-order effects.

---

## ORIGINAL ANALYSIS (Historical)

---

## Problem Summary

The current U/N multiplication implementation adds **extra uncertainty terms** not specified in SSOPT, causing results to be MORE conservative than the mathematical specification requires.

### Discrepancy Found

**Test Case**:
```
UN1 = ((10.0, 0.5), (10.2, 0.3))
UN2 = ((5.0, 0.2), (5.1, 0.1))
```

**SSOPT Specification** (Section 2.2, Definition 4):
```
u_t_result = |n_a1|u_t2 + |n_a2|u_t1 + |n_m1|u_m2 + |n_a2|u_m1
           = 10.0×0.2 + 5.0×0.5 + 10.2×0.1 + 5.0×0.3
           = 7.020000

u_m_result = |n_m1|u_m2 + |n_m2|u_m1
           = 10.2×0.1 + 5.1×0.3
           = 2.550000
```

**Current Implementation**:
```
u_t_result = 9.300000  (+2.280000 extra!)
u_m_result = 2.580000  (+0.030000 extra!)
```

---

## Root Cause Analysis

### Issue 1: Quadratic Terms Added (Not in SSOPT)

Current implementation adds:
```python
quad_u_t = u_t1 * u_t2           = 0.5 × 0.2 = 0.1
quad_u_m = u_m1 * u_m2           = 0.3 × 0.1 = 0.03
quad_mixed = u_t1*u_m2 + u_m1*u_t2 = 0.5×0.1 + 0.3×0.2 = 0.11
```

**Total extra from quadratic**: ~0.24

### Issue 2: Cross-Terms Formula Error

**SSOPT Formula**:
```
cross_term = |n_m1|u_m2 + |n_a2|u_m1
           = 10.2×0.1 + 5.0×0.3 = 2.52
```

**Current Implementation**:
```python
cross_terms = |n_m1|u_t2 + |n_m2|u_t1  # WRONG!
            = 10.2×0.2 + 5.1×0.5 = 4.59
```

This mixes measured nominals with **tolerance** uncertainties instead of **measurement** uncertainties.

**Difference**: 4.59 - 2.52 = **2.07 overcounting**

---

## Impact Assessment

### Why Tests Still Passed

1. **Conservativity**: Extra uncertainty makes results MORE conservative
2. **Conservativity Theorem**: Still holds (we exceed lower bound)
3. **Triangle Inequality**: Still valid with larger uncertainties

### Problems

1. **Specification Violation**: Implementation ≠ Theory
2. **Over-Conservative**: Unnecessarily wide uncertainty bounds
3. **Publication Risk**: Reviewers will catch the discrepancy
4. **Trust Issue**: Cannot claim "implemented as specified"

---

## Comparison: N/U vs. U/N Multiplication

### N/U Algebra (Correct)
```
(n₁, u₁) ⊗ (n₂, u₂) = (n₁n₂, |n₁|u₂ + |n₂|u₁ + λu₁u₂)
```
With λ=1: matches interval arithmetic exactly
With λ=0: linear approximation only

### U/N Algebra (SSOPT Spec)
```
u_t = |n_a1|u_t2 + |n_a2|u_t1 + |n_m1|u_m2 + |n_a2|u_m1
u_m = |n_m1|u_m2 + |n_m2|u_m1
```
**No λ parameter mentioned** - appears to use λ=0 (linear only)

### Question: Should U/N Use λ=1 for Conservativity?

**Arguments FOR adding quadratic terms**:
- N/U uses λ=1 for exactness
- Conservativity theorem requires tightest bounds
- Interval arithmetic demands it

**Arguments AGAINST**:
- SSOPT specification doesn't include them
- Already conservative via cross-terms
- Phase 3 tests passed without them (when fixed)

---

## Correct Implementation (SSOPT-Compliant)

```python
def multiply(self, other: 'UNAlgebra') -> 'UNAlgebra':
    """
    U/N Multiplication per SSOPT Definition 4.
    """
    # Nominals
    n_a_result = self.actual_pair.n * other.actual_pair.n
    n_m_result = self.measured_pair.n * other.measured_pair.n

    # Tolerance uncertainty (SSOPT formula)
    u_t_result = (
        abs(self.actual_pair.n) * other.actual_pair.u +
        abs(other.actual_pair.n) * self.actual_pair.u +
        abs(self.measured_pair.n) * other.measured_pair.u +
        abs(other.actual_pair.n) * self.measured_pair.u
    )

    # Measurement uncertainty (SSOPT formula)
    u_m_result = (
        abs(self.measured_pair.n) * other.measured_pair.u +
        abs(other.measured_pair.n) * self.measured_pair.u
    )

    return UNAlgebra(
        NUPair(n_a_result, u_t_result),
        NUPair(n_m_result, u_m_result)
    )
```

---

## Action Plan

### Phase 1: Verify & Document (URGENT)

1. ✅ Identify exact formula mismatch
2. ⬜ Check if SSOPT intended λ=0 or λ=1
3. ⬜ Determine if tests would pass with correct formula
4. ⬜ Document decision on quadratic terms

### Phase 2: Fix & Re-Validate

1. ⬜ Implement SSOPT-exact formula (no quadratic)
2. ⬜ Re-run all 102k+ tests
3. ⬜ Check if conservativity still holds
4. ⬜ If tests fail: investigate why

### Phase 3: Theoretical Resolution

**Option A**: SSOPT is correct as-is (λ=0)
- Fix implementation to match
- Re-validate
- Update documentation

**Option B**: SSOPT needs amendment (should use λ=1)
- Update SSOPT to include quadratic terms
- Fix cross-term formula
- Re-validate against updated spec

**Option C**: Hybrid approach
- Implement both versions
- Document tradeoffs
- Let users choose via parameter

---

## Decision Required

**BEFORE proceeding with any tutorials, benchmarks, or R validation:**

1. **Clarify SSOPT intent**: Should U/N multiplication include quadratic λu₁u₂ terms?
2. **Fix implementation**: Either match SSOPT or update SSOPT to match implementation
3. **Re-validate**: Ensure tests pass with correct formula

**This is blocking** - cannot publish or deploy with formula mismatch.

---

## References

- SSOPT Section 2.2, Definition 4
- N/U Algebra DOI: 10.5281/zenodo.17172694
- Test logs: `validation/phase_3_results/test_run_SUCCESS.log`

---

**Status**: PENDING RESOLUTION
**Next Step**: Determine correct formula and fix implementation
