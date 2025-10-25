# U/N Algebra: Uncertainty/Nominal Algebra Framework

[![License](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/Tests-102k%20passed-success)](validation/PHASE_3_VALIDATION_REPORT.md)
[![Version](https://img.shields.io/badge/Version-1.0.0--beta-blue)](VERSION)

## Overview

**U/N Algebra** is the complementary dual to N/U Algebra, representing quantities as **nested N/U pairs** ((n_a, u_t), (n_m, u_m)) where uncertainty models second-order epistemic structure.

**Key Features:**
- **Interval-exact multiplication** (λ=1 default) with proper u×u quadratic terms
- **Cross-tier guard** preserving triangle inequality: |n_m - n_a| ≤ u_t + u_m
- **Compatibility mode** (λ=0) for linear-only N/U-style operations
- **Empirically validated:** 102,000+ test cases with zero failures

## Quick Start

### Python
```python
from un_algebra.core import create_UN, hubble_UN_merge

# Create U/N values
early = create_UN(n_a=67.4, u_t=0.3, n_m=67.4, u_m=0.5)
late = create_UN(n_a=73.0, u_t=0.4, n_m=73.0, u_m=1.0)

# Multiplication with default λ=1 (interval-exact, recommended)
product = early.multiply(late)

# Or use λ=0 for linear-only (N/U compatibility mode)
product_linear = early.multiply(late, lam=0.0)

# Merge with tensor distance for cosmology
result = hubble_UN_merge(early, late, tensor_distance=1.3)
```

### The λ Parameter

U/N multiplication supports two modes via the `lam` parameter:

- **λ=1.0 (default):** Interval-exact, includes quadratic uncertainty terms (u×u)
  - Recommended for all uncertainty-critical applications
  - Properly models second-order compounding
  - Matches symmetric-interval product semantics: [a±Δa]×[b±Δb]

- **λ=0.0:** Linear-only, first-order Taylor approximation
  - For compatibility testing with classical N/U operations
  - May underestimate uncertainty in deep operation chains

See [docs/SSOPT.md](docs/SSOPT.md) for the complete mathematical specification.
