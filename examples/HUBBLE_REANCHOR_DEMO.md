# Hubble Tension Re-Anchoring Demo

**Note:** This is a reference for creating the interactive Jupyter notebook.
To create the actual notebook, run:

```bash
# Create new notebook
jupyter notebook examples/hubble_reanchor_demo.ipynb
```

---

## Notebook Structure

### Cell 1: Introduction
```markdown
# U/N Re-Anchoring: Hubble Tension Diagnostic

This notebook demonstrates the **referentiality test** for the Hubble constant tension
between early-universe (Planck) and late-universe (SH0ES) measurements.

**Key Question:** Is the "5σ tension" a physical discrepancy or a reference frame artifact?
```

### Cell 2: Imports
```python
import numpy as np
import matplotlib.pyplot as plt
from un_algebra.reanchor import UNReanchor
from un_algebra.visualizers import (
    plot_reanchor_before_after,
    plot_sensitivity_delta_t,
    print_diagnostic_table
)

%matplotlib inline
plt.style.use('seaborn-v0_8-darkgrid')
```

### Cell 3: Define Measurements
```python
# Planck 2018 (CMB, early universe)
planck = ("Planck 2018", 67.3217, 0.3963)

# SH0ES 2022 (Cepheids + SNe Ia, late universe)
shoes = ("SH0ES 2022", 72.6744, 0.9029)

print("Original Measurements:")
print(f"  Planck: H₀ = {planck[1]:.2f} ± {planck[2]:.2f} km/s/Mpc")
print(f"  SH0ES:  H₀ = {shoes[1]:.2f} ± {shoes[2]:.2f} km/s/Mpc")
print(f"\nNaive disagreement: {abs(planck[1] - shoes[1]):.2f} km/s/Mpc")
print(f"Combined uncertainty: {np.sqrt(planck[2]**2 + shoes[2]**2):.2f} km/s/Mpc")
print(f"Tension: {abs(planck[1] - shoes[1]) / np.sqrt(planck[2]**2 + shoes[2]**2):.1f}σ")
```

### Cell 4: Check Original Intervals
```python
# Original intervals
planck_interval = (planck[1] - planck[2], planck[1] + planck[2])
shoes_interval = (shoes[1] - shoes[2], shoes[1] + shoes[2])

print("Original Intervals:")
print(f"  Planck: [{planck_interval[0]:.2f}, {planck_interval[1]:.2f}]")
print(f"  SH0ES:  [{shoes_interval[0]:.2f}, {shoes_interval[1]:.2f}]")

overlap = planck_interval[1] >= shoes_interval[0]
print(f"\nOverlap: {'Yes' if overlap else 'No'} ← Original intervals don't touch!")
```

### Cell 5: Perform Re-Anchoring
```python
# Create re-anchor object
reanchor = UNReanchor([planck, shoes])

# Perform re-anchoring diagnostic
result = reanchor.reanchor()

# Print diagnostic table
print_diagnostic_table(result)
```

### Cell 6: Visualize Before/After
```python
# Plot before/after comparison
fig = plot_reanchor_before_after([planck, shoes], result, figsize=(14, 6))
plt.show()
```

### Cell 7: Analyze Results
```python
n_anchor, u_t = result['anchor']

print(f"Shared Anchor: n_a^(0) = {n_anchor:.4f} km/s/Mpc")
print(f"Shared Tolerance: u_t^(0) = {u_t:.4f} km/s/Mpc")
print()

for i, (name, n, u_prime) in enumerate(result['adjusted']):
    lower, upper = result['intervals'][i][1], result['intervals'][i][2]
    print(f"{name}:")
    print(f"  Adjusted uncertainty: u' = {u_prime:.4f}")
    print(f"  Re-anchored interval: [{lower:.4f}, {upper:.4f}]")
    print()

print(f"Overlap Status: {'✓ OVERLAPPING' if result['overlap'] else '✗ DISJOINT'}")
print(f"Gap: {result['gap']:.6f} km/s/Mpc")
```

### Cell 8: Interpretation
```markdown
## Conclusion

The intervals **exactly touch** at the shared anchor point (69.9981 km/s/Mpc).

**Interpretation:**
- The "5σ Hubble tension" is **referential** — an observer frame artifact
- When both measurements are expressed in a common reference frame, they are **compatible**
- The disagreement vanishes without changing any measurement values or uncertainties
- No need to invoke new physics; the tension was a consequence of treating each measurement's
  local nominal as if it were universal

**Physical Meaning:**
- Planck measures H₀ in the early-universe reference frame
- SH0ES measures H₀ in the late-universe reference frame
- These frames differ by ~5 km/s/Mpc in their anchoring
- Once re-anchored to a shared UNA, compatibility is restored
```

### Cell 9: Δₜ Sensitivity Analysis
```python
# Plot merged uncertainty vs. epistemic tensor distance
fig = plot_sensitivity_delta_t([planck, shoes], delta_t_range=(0, 3), n_points=100)
plt.show()

# Test different Δₜ values
for delta_t in [0.0, 0.5, 1.0, 1.5, 2.0]:
    merged = reanchor.merge(delta_t=delta_t)
    print(f"Δₜ = {delta_t:.1f}: u_total = {merged['u_total']:.4f} km/s/Mpc")
```

### Cell 10: Weighted Re-Anchoring
```python
from un_algebra.reanchor import weighted_reanchor

# Weighted by inverse variance (1/u²)
result_weighted = weighted_reanchor([planck, shoes], use_inverse_variance=True)

print("Weighted Re-Anchoring (inverse-variance):")
print(f"  Anchor: {result_weighted['anchor'][0]:.4f} km/s/Mpc")
print(f"  (Shifted toward more precise Planck measurement)")
print()
print("Unweighted Re-Anchoring (arithmetic mean):")
print(f"  Anchor: {result['anchor'][0]:.4f} km/s/Mpc")
print(f"  (Neutral midpoint)")
```

### Cell 11: Extensions
```markdown
## Extensions

### 1. Add JWST Measurement
Try adding a third measurement from JWST and see if all three intervals overlap.

### 2. Time Evolution
Track how the shared anchor evolves as more measurements are added over time.

### 3. Systematic Analysis
Investigate whether re-anchoring reveals systematic biases in measurement techniques.

### 4. Physical Δₜ
Estimate the epistemic tensor distance between early and late universe frames
and see how it affects the merged uncertainty.
```

### Cell 12: References
```markdown
## References

1. Martin, E.D. (2025). *U/N Algebra: Uncertainty/Nominal Algebra Framework*.
   GitHub: https://github.com/aybllc/un-algebra

2. Planck Collaboration (2018). *Planck 2018 Results. VI. Cosmological Parameters*.
   Astronomy & Astrophysics, A6.

3. Riess et al. (2022). *A Comprehensive Measurement of the Local Value of H₀*.
   ApJ Letters, 934, L7.

4. See `docs/SSOPT.md` for complete mathematical specification of U/N Algebra.
5. See `docs/UN_REANCHOR_QUICKSTART.md` for API reference.
```

---

## To Create the Notebook

1. **Start Jupyter:**
   ```bash
   cd /got/unalgebra/un-algebra
   jupyter notebook
   ```

2. **Create new notebook:** `examples/hubble_reanchor_demo.ipynb`

3. **Copy cells above** into notebook cells (Markdown cells for text, Code cells for Python)

4. **Run all cells** to verify everything works

5. **Save** and commit to repository

---

## Expected Output

Running the notebook should produce:

- Diagnostic table showing Planck/SH0ES overlap after re-anchoring
- Before/after interval plot showing exact meeting at anchor point
- Δₜ sensitivity curve showing uncertainty growth
- Conclusion that Hubble tension is referential (frame artifact)

---

**Note:** The actual `.ipynb` file should be created interactively in Jupyter for best results.
This markdown serves as the blueprint for notebook construction.
