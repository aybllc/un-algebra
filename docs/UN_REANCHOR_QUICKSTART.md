# U/N Re-Anchoring: Quickstart Guide

**Version:** 1.0-beta
**Author:** Eric D. Martin
**License:** CC BY 4.0

---

## Table of Contents

1. [What is Re-Anchoring?](#what-is-re-anchoring)
2. [Installation](#installation)
3. [Quick Example](#quick-example)
4. [Core Concepts](#core-concepts)
5. [API Reference](#api-reference)
6. [Visualization](#visualization)
7. [Use Cases](#use-cases)
8. [FAQ](#faq)

---

## What is Re-Anchoring?

**Re-anchoring** is a diagnostic test for determining whether apparent tension between measurements is **referential** (a reference frame artifact) or **physical** (genuinely incompatible).

### The Problem

Two measurements may appear incompatible when each uses its own local reference frame (different `n_a` values). For example:

- **Planck (early universe):** H₀ = 67.32 ± 0.40 km/s/Mpc
- **SH0ES (late universe):** H₀ = 72.67 ± 0.90 km/s/Mpc

These intervals **don't overlap**, suggesting a "Hubble tension."

### The Diagnostic

Re-anchoring moves both measurements to a **shared Universal Nominal Anchor (UNA)** and applies minimal uncertainty adjustments to preserve the triangle inequality:

```
|n_i - n_a^(0)| ≤ u_t^(0) + u_i'
```

If intervals **overlap** after re-anchoring → tension is **referential**
If intervals **remain disjoint** → tension is **physical**

---

## Installation

The re-anchoring module is part of the U/N Algebra package:

```bash
cd /got/unalgebra/un-algebra
pip install -e .
```

### Dependencies

- Python 3.8+
- numpy
- matplotlib (for visualization)
- pytest (for tests)

---

## Quick Example

### Hubble Tension Diagnostic

```python
from un_algebra.reanchor import UNReanchor

# Define measurements (name, nominal, uncertainty)
planck = ("Planck", 67.3217, 0.3963)
shoes = ("SH0ES", 72.6744, 0.9029)

# Create re-anchor object
reanchor = UNReanchor([planck, shoes])

# Perform re-anchoring
result = reanchor.reanchor()

# Check overlap status
print(f"Overlap: {result['overlap']}")  # True
print(f"Gap: {result['gap']}")          # 0.0

# View intervals
for name, lower, upper in result['intervals']:
    print(f"{name}: [{lower:.4f}, {upper:.4f}]")
```

**Output:**
```
Overlap: True
Gap: 0.0
Planck: [64.6454, 69.9981]
SH0ES: [69.9981, 75.3508]
```

**Conclusion:** The Hubble tension is **referential** — intervals touch exactly after re-anchoring.

---

## Core Concepts

### 1. Shared Universal Nominal Anchor (UNA)

The shared anchor `n_a^(0)` is computed as:

- **Unweighted:** Arithmetic mean of all measurements
- **Weighted:** Inverse-variance weighted mean: `w_i = 1/u_i²`
- **Explicit:** User-provided anchor point

### 2. Minimal Triangle-Inequality Adjustment

For each measurement, if the triangle inequality is violated:

```
d_i = |n_i - n_a^(0)|
if d_i > u_t^(0) + u_i:
    u_i' = u_i + (d_i - (u_t^(0) + u_i))
else:
    u_i' = u_i
```

This ensures: `|n_i - n_a^(0)| ≤ u_t^(0) + u_i'`

### 3. Projection to N/U Space

Each adjusted measurement is projected:

```
π_i = (n_i, u_t^(0) + u_i')
```

Giving interval bounds:

```
[n_i - (u_t^(0) + u_i'), n_i + (u_t^(0) + u_i')]
```

### 4. Overlap Detection

Intervals are checked for touching/overlapping. If all intervals touch or overlap, the tension is referential.

---

## API Reference

### `UNReanchor` Class

```python
class UNReanchor:
    """Re-anchor measurements to shared Universal Nominal Anchor."""

    def __init__(self, datasets: List[Tuple[str, float, float]]):
        """
        Parameters:
            datasets: List of (name, nominal, uncertainty) tuples
        """

    def reanchor(self,
                 weights: Optional[List[float]] = None,
                 shared_anchor: Optional[Tuple[float, float]] = None) -> Dict:
        """
        Perform re-anchoring to shared UNA.

        Parameters:
            weights: Optional weights for computing anchor (default: None = unweighted)
            shared_anchor: Optional explicit (n_anchor, u_t) tuple

        Returns:
            Dictionary with keys:
                - anchor: (n_anchor, u_t)
                - adjusted: List of (name, n, u') tuples
                - projections: List of (name, n, u_proj) N/U projections
                - intervals: List of (name, lower, upper)
                - overlap: Boolean (True if intervals touch/overlap)
                - gap: Minimum gap between intervals (0 if overlapping)
        """

    def merge(self, delta_t: float = 0.0) -> Dict:
        """
        Merge re-anchored measurements with epistemic expansion.

        Parameters:
            delta_t: Epistemic tensor distance (default 0)

        Returns:
            Dictionary with keys:
                - n_merged: Merged nominal (at anchor)
                - u_std: Standard uncertainty component
                - u_expand: Epistemic expansion component
                - u_total: Total merged uncertainty
                - interval: (lower, upper) bounds
        """
```

### Convenience Functions

```python
def reanchor_pairwise(n1: float, u1: float, n2: float, u2: float) -> Dict:
    """Quick pairwise re-anchoring for two measurements."""

def weighted_reanchor(datasets: List[Tuple[str, float, float]],
                      use_inverse_variance: bool = True) -> Dict:
    """Re-anchor with inverse-variance weighting."""
```

---

## Visualization

### Before/After Interval Plot

```python
from un_algebra.visualizers import plot_reanchor_before_after

datasets = [("Planck", 67.3217, 0.3963), ("SH0ES", 72.6744, 0.9029)]
fig = plot_reanchor_before_after(datasets)
fig.savefig('reanchor_before_after.png')
```

**Shows:**
- Left panel: Original intervals (may not overlap)
- Right panel: Re-anchored intervals with shared UNA marked
- Overlap status annotation

### Δₜ Sensitivity Sweep

```python
from un_algebra.visualizers import plot_sensitivity_delta_t

fig = plot_sensitivity_delta_t(datasets, delta_t_range=(0, 2))
fig.savefig('delta_t_sensitivity.png')
```

**Shows:**
- How merged uncertainty grows with epistemic tensor distance
- Separate curves for `u_std`, `u_expand`, and `u_total`

### Multiway Compass Plot

```python
from un_algebra.visualizers import plot_multiway_compass

three_datasets = [("A", 65, 0.5), ("B", 70, 0.8), ("C", 75, 0.6)]
fig = plot_multiway_compass(three_datasets)
fig.savefig('multiway_compass.png')
```

**Shows:**
- Polar plot with each dataset as vector from anchor
- Shared tolerance circle marked

### Diagnostic Table

```python
from un_algebra.visualizers import print_diagnostic_table

reanchor = UNReanchor(datasets)
result = reanchor.reanchor()
print_diagnostic_table(result)
```

**Prints:**
- Shared anchor values
- Adjusted uncertainties table
- Intervals with bounds
- Overlap status and interpretation

---

## Use Cases

### 1. Cosmology: Hubble Constant Tension

```python
planck = ("Planck 2018", 67.32, 0.40)
shoes = ("SH0ES 2022", 72.67, 0.90)
jwst = ("JWST 2024", 70.5, 1.2)

reanchor = UNReanchor([planck, shoes, jwst])
result = reanchor.reanchor()

if result['overlap']:
    print("→ Hubble tension is referential (observer frame artifact)")
else:
    print(f"→ Physical tension remains (gap: {result['gap']:.4f})")
```

### 2. Multi-Lab Calibration

```python
lab_a = ("Lab A", 9.807, 0.002)
lab_b = ("Lab B", 9.809, 0.003)
lab_c = ("Lab C", 9.805, 0.001)

result = weighted_reanchor([lab_a, lab_b, lab_c])
print(f"Consensus: {result['anchor'][0]:.4f} ± {result['anchor'][1]:.4f}")
```

### 3. Time-Series Reconciliation

```python
measurements = [
    ("2020", 100.5, 0.5),
    ("2021", 101.2, 0.4),
    ("2022", 102.0, 0.6),
    ("2023", 101.8, 0.3)
]

reanchor = UNReanchor(measurements)
result = reanchor.reanchor()

# Check for systematic drift
if result['overlap']:
    print("→ Variations within reference frame ambiguity")
else:
    print("→ Systematic drift detected")
```

---

## FAQ

### Q: When should I use re-anchoring vs. standard error propagation?

**A:** Use re-anchoring as a **diagnostic first step**. If tension is referential, proceed with re-anchored values for merging/fitting. If tension is physical, investigate systematic errors or new physics.

### Q: What does "overlap" mean exactly?

**A:** Intervals are considered overlapping if their bounds touch (gap ≤ numerical tolerance ~1e-10) or intersect.

### Q: Can I specify my own anchor point?

**A:** Yes, pass `shared_anchor=(n_anchor, u_t)` to `reanchor()`:

```python
result = reanchor.reanchor(shared_anchor=(70.0, 1.0))
```

### Q: What is Δₜ (delta_t)?

**A:** Epistemic tensor distance from the Observer Domain formalism. It quantifies how "far apart" two reference frames are epistemically. Use `delta_t=0` for pure anchor-based reconciliation.

### Q: Does re-anchoring work with >2 datasets?

**A:** Yes, it generalizes naturally to N datasets via weighted barycenter. See multiway examples above.

### Q: How do I choose between weighted and unweighted?

**A:** Use **weighted** (inverse-variance) when measurements have different precisions. Use **unweighted** when all measurements are equally trustworthy or for neutral diagnostic tests.

### Q: What if intervals don't overlap after re-anchoring?

**A:** This indicates **physical tension** — the measurements are genuinely incompatible beyond reference frame effects. Investigate:
1. Systematic errors in measurements
2. Model assumptions (e.g., cosmological parameters)
3. New physics (e.g., early vs. late universe physics)

---

## Testing

Run the full test suite:

```bash
pytest src/python/tests/test_reanchor.py -v
```

**Expected:** 22 tests passing (100%)

---

## Citation

If you use this re-anchoring diagnostic in your research, please cite:

```bibtex
@software{martin2025unalgebra,
  author = {Martin, Eric D.},
  title = {U/N Algebra: Uncertainty/Nominal Algebra Framework},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/aybllc/un-algebra},
  doi = {10.5281/zenodo.XXXXXXX}
}
```

---

## Support

- **GitHub:** https://github.com/aybllc/un-algebra
- **Issues:** https://github.com/aybllc/un-algebra/issues
- **Documentation:** /got/unalgebra/un-algebra/docs/

---

## Next Steps

1. **Tutorial Notebook:** See `examples/hubble_reanchor_demo.ipynb` for interactive walkthrough
2. **Full SSOPT:** See `docs/SSOPT.md` for complete mathematical specification
3. **Phase 3 Validation:** See `validation/PHASE_3_VALIDATION_REPORT.md` for empirical testing

---

**All Your Baseline LLC**
*CC BY 4.0 License*
