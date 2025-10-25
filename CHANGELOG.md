# Changelog

## [1.0.0-beta] - 2025-10-24

### Phase 3: Validation ✅ COMPLETE
- **102,000+ tests executed - ZERO failures**
- **100.00% success rate**
- Fixed triangle inequality enforcement in random generator
- Fixed conservativity projection (use n_a_known=False)
- Runtime: 0.50 seconds
- PAC confidence established

### Canonical λ=1 Specification (Interval-Exact)
- **Added λ parameter to multiply() method** (default=1.0)
- **Canonical formula includes quadratic uncertainty terms (u×u)**:
  - u_t = |n_a1|u_t2 + |n_a2|u_t1 + λu_t1u_t2 + |n_m1|u_t2 + |n_m2|u_t1 + λ(u_t1u_m2 + u_m1u_t2)
  - u_m = |n_m1|u_m2 + |n_m2|u_m1 + λu_m1u_m2
- **λ=1.0 (default):** Interval-exact, conservative (recommended)
- **λ=0.0:** Linear-only, N/U compatibility mode
- Verified implementation matches specification (zero test failures)
- Updated SSOPT documentation with canonical formula
- Updated README with λ parameter examples

## [1.0.0-alpha] - 2025-10-24

### Phase 1: Formalization ✅
- SSOPT specification
- PAC coverage proofs

### Phase 2: Implementation ✅
- Python core (450 lines)
- R companion (380 lines)
- 102k test suite designed
