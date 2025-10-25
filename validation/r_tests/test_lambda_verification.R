# R Validation: λ Parameter Cross-Check with Python
#
# Verifies R implementation matches Python canonical specification
#
# Expected Python results (from /tmp/verify_lambda1.py):
#   λ=1: u_t=9.300000, u_m=2.580000
#   λ=0: u_t=9.090000, u_m=2.550000

library(testthat)
source("src/r/un_algebra.R")

test_that("R implementation matches Python λ=1 canonical", {
  # Test case from Python verification
  n_a1 <- 10.0
  u_t1 <- 0.5
  n_m1 <- 10.2
  u_m1 <- 0.3

  n_a2 <- 5.0
  u_t2 <- 0.2
  n_m2 <- 5.1
  u_m2 <- 0.1

  un1 <- UNAlgebra(n_a1, u_t1, n_m1, u_m1)
  un2 <- UNAlgebra(n_a2, u_t2, n_m2, u_m2)

  # Test λ=1 (default, canonical)
  result_lambda1 <- un_multiply(un1, un2, lam = 1.0)

  # Expected values from Python
  expected_u_t <- 9.300000
  expected_u_m <- 2.580000

  cat("\n=======================================\n")
  cat("R λ=1 CANONICAL VERIFICATION\n")
  cat("=======================================\n")
  cat(sprintf("R Result:  u_t = %.6f, u_m = %.6f\n",
              result_lambda1$actual_pair$u,
              result_lambda1$measured_pair$u))
  cat(sprintf("Python:    u_t = %.6f, u_m = %.6f\n",
              expected_u_t, expected_u_m))

  # Tolerance: 1e-10 (extremely tight numerical agreement)
  tol <- 1e-10

  expect_equal(result_lambda1$actual_pair$u, expected_u_t, tolerance = tol,
               info = "u_t must match Python λ=1")
  expect_equal(result_lambda1$measured_pair$u, expected_u_m, tolerance = tol,
               info = "u_m must match Python λ=1")

  cat("✓ R matches Python for λ=1 (interval-exact)\n")
})

test_that("R implementation matches Python λ=0 compatibility mode", {
  n_a1 <- 10.0
  u_t1 <- 0.5
  n_m1 <- 10.2
  u_m1 <- 0.3

  n_a2 <- 5.0
  u_t2 <- 0.2
  n_m2 <- 5.1
  u_m2 <- 0.1

  un1 <- UNAlgebra(n_a1, u_t1, n_m1, u_m1)
  un2 <- UNAlgebra(n_a2, u_t2, n_m2, u_m2)

  # Test λ=0 (linear-only, compatibility)
  result_lambda0 <- un_multiply(un1, un2, lam = 0.0)

  # Expected values from Python
  expected_u_t <- 9.090000
  expected_u_m <- 2.550000

  cat("\n=======================================\n")
  cat("R λ=0 COMPATIBILITY MODE VERIFICATION\n")
  cat("=======================================\n")
  cat(sprintf("R Result:  u_t = %.6f, u_m = %.6f\n",
              result_lambda0$actual_pair$u,
              result_lambda0$measured_pair$u))
  cat(sprintf("Python:    u_t = %.6f, u_m = %.6f\n",
              expected_u_t, expected_u_m))

  tol <- 1e-10

  expect_equal(result_lambda0$actual_pair$u, expected_u_t, tolerance = tol,
               info = "u_t must match Python λ=0")
  expect_equal(result_lambda0$measured_pair$u, expected_u_m, tolerance = tol,
               info = "u_m must match Python λ=0")

  cat("✓ R matches Python for λ=0 (linear-only)\n")
})

test_that("Triangle inequality preserved through multiplication", {
  set.seed(42)

  n_passes <- 0
  n_total <- 1000

  for (i in 1:n_total) {
    # Generate random valid U/N values
    n_a1 <- runif(1, -100, 100)
    n_m1 <- runif(1, -100, 100)
    u_t1 <- runif(1, 0, 10)
    u_m1 <- runif(1, 0, 10)

    # Enforce triangle inequality on input
    diff1 <- abs(n_m1 - n_a1)
    if (diff1 > u_t1 + u_m1) {
      u_m1 <- diff1 - u_t1 + 0.1
    }

    n_a2 <- runif(1, -100, 100)
    n_m2 <- runif(1, -100, 100)
    u_t2 <- runif(1, 0, 10)
    u_m2 <- runif(1, 0, 10)

    diff2 <- abs(n_m2 - n_a2)
    if (diff2 > u_t2 + u_m2) {
      u_m2 <- diff2 - u_t2 + 0.1
    }

    un1 <- UNAlgebra(n_a1, u_t1, n_m1, u_m1)
    un2 <- UNAlgebra(n_a2, u_t2, n_m2, u_m2)

    # Multiply with λ=1
    result <- un_multiply(un1, un2, lam = 1.0)

    # Check triangle inequality on result
    if (un_triangle_check(result)) {
      n_passes <- n_passes + 1
    }
  }

  cat(sprintf("\nTriangle inequality tests: %d/%d passed\n", n_passes, n_total))
  expect_equal(n_passes, n_total,
               info = "All products must preserve triangle inequality")
})

# Run tests
cat("\n")
cat("==============================================\n")
cat("R VALIDATION: λ Parameter Cross-Check\n")
cat("==============================================\n")
cat("Testing R implementation against Python...\n\n")

test_file(system.file("validation/r_tests/test_lambda_verification.R",
                      package = "un_algebra"),
          reporter = "summary")
