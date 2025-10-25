# U/N Algebra: R Implementation
# Uncertainty/Nominal Algebra for R
#
# Author: Eric D. Martin
# Version: 1.0 Alpha
# License: CC BY 4.0
#
# Companion to Python implementation with equivalent operations

# ===== S3 CLASS: NUPair =====

#' N/U Pair Class
#'
#' Represents a standard N/U pair (nominal, uncertainty)
#'
#' @param n Nominal value (numeric)
#' @param u Uncertainty bound (numeric, must be >= 0)
#'
#' @return Object of class "NUPair"
#'
#' @examples
#' np <- NUPair(10.5, 0.3)
#' print(np)
#'
#' @export
NUPair <- function(n, u) {
  u <- max(0, u)  # Enforce non-negativity
  
  obj <- list(
    n = as.numeric(n),
    u = as.numeric(u)
  )
  class(obj) <- "NUPair"
  return(obj)
}

#' @export
print.NUPair <- function(x, ...) {
  cat(sprintf("NU(n=%.6f, u=%.6f)\n", x$n, x$u))
  invisible(x)
}

#' N/U Pair Addition
#' @export
`+.NUPair` <- function(x, y) {
  if (!inherits(y, "NUPair")) {
    stop("Can only add NUPair objects")
  }
  return(NUPair(x$n + y$n, x$u + y$u))
}

#' N/U Pair Multiplication
#' @export
`*.NUPair` <- function(x, y) {
  if (inherits(y, "NUPair")) {
    n_prod <- x$n * y$n
    u_prod <- abs(x$n) * y$u + abs(y$n) * x$u
    return(NUPair(n_prod, u_prod))
  } else if (is.numeric(y)) {
    return(NUPair(x$n * y, abs(y) * x$u))
  }
  stop("Invalid multiplication")
}

#' @export
`*.numeric` <- function(x, y) {
  if (inherits(y, "NUPair")) {
    return(y * x)
  }
  return(base::`*`(x, y))
}

#' Invariant M for N/U pair
#' @export
invariant_M.NUPair <- function(x) {
  return(abs(x$n) + x$u)
}

# ===== S3 CLASS: UNAlgebra =====

#' U/N Algebra Element
#'
#' Represents U/N pair: ((n_a, u_t), (n_m, u_m))
#'
#' @param n_a Nominal actual value
#' @param u_t Tolerance/epistemic uncertainty
#' @param n_m Nominal measured value
#' @param u_m Measurement uncertainty
#'
#' @return Object of class "UNAlgebra"
#'
#' @examples
#' un <- UNAlgebra(10.0, 0.5, 10.1, 0.2)
#' print(un)
#'
#' @export
UNAlgebra <- function(n_a, u_t, n_m, u_m) {
  u_t <- max(0, u_t)
  u_m <- max(0, u_m)
  
  obj <- list(
    actual_pair = NUPair(n_a, u_t),
    measured_pair = NUPair(n_m, u_m)
  )
  class(obj) <- "UNAlgebra"
  return(obj)
}

#' @export
print.UNAlgebra <- function(x, ...) {
  cat(sprintf(
    "UN((n_a=%.4f, u_t=%.4f), (n_m=%.4f, u_m=%.4f))\n",
    x$actual_pair$n, x$actual_pair$u,
    x$measured_pair$n, x$measured_pair$u
  ))
  invisible(x)
}

# ===== CORE OPERATIONS =====

#' U/N Addition
#'
#' @param un1 First U/N value
#' @param un2 Second U/N value
#'
#' @return Result U/N value
#'
#' @export
un_add <- function(un1, un2) {
  if (!inherits(un1, "UNAlgebra") || !inherits(un2, "UNAlgebra")) {
    stop("Both arguments must be UNAlgebra objects")
  }
  
  actual_result <- un1$actual_pair + un2$actual_pair
  measured_result <- un1$measured_pair + un2$measured_pair
  
  obj <- list(
    actual_pair = actual_result,
    measured_pair = measured_result
  )
  class(obj) <- "UNAlgebra"
  return(obj)
}

#' U/N Addition (operator)
#'
#' @export
`+.UNAlgebra` <- function(x, y) {
  return(un_add(x, y))
}

#' U/N Multiplication (Interval-Exact with λ Parameter)
#'
#' U/N multiplication with uncertainty-first propagation and cross-tier guard.
#'
#' @param un1 First U/N value
#' @param un2 Second U/N value
#' @param lam Lambda parameter controlling quadratic uncertainty terms (default 1.0)
#'   - λ=1.0 (default): Interval-exact, includes u×u quadratic terms (recommended)
#'   - λ=0.0: Linear-only, N/U compatibility mode
#'
#' @return Result U/N value
#'
#' @details
#' Canonical formula (λ=1):
#'   u_t = |n_a1|u_t2 + |n_a2|u_t1 + λu_t1u_t2              [tier terms]
#'       + |n_m1|u_t2 + |n_m2|u_t1 + λ(u_t1u_m2 + u_m1u_t2) [cross-tier guard]
#'   u_m = |n_m1|u_m2 + |n_m2|u_m1 + λu_m1u_m2              [tier terms]
#'
#' @export
un_multiply <- function(un1, un2, lam = 1.0) {
  if (!inherits(un1, "UNAlgebra") || !inherits(un2, "UNAlgebra")) {
    stop("Both arguments must be UNAlgebra objects")
  }

  n_a1 <- un1$actual_pair$n
  u_t1 <- un1$actual_pair$u
  n_m1 <- un1$measured_pair$n
  u_m1 <- un1$measured_pair$u

  n_a2 <- un2$actual_pair$n
  u_t2 <- un2$actual_pair$u
  n_m2 <- un2$measured_pair$n
  u_m2 <- un2$measured_pair$u

  # Nominals
  n_a_result <- n_a1 * n_a2
  n_m_result <- n_m1 * n_m2

  # Tier terms (within-frame propagation)
  u_t_tier <- abs(n_a1) * u_t2 + abs(n_a2) * u_t1
  u_m_tier <- abs(n_m1) * u_m2 + abs(n_m2) * u_m1

  # Cross-tier guard (epistemic coupling)
  cross_linear <- abs(n_m1) * u_t2 + abs(n_m2) * u_t1

  # Quadratic terms (controlled by λ)
  quad_u_t <- lam * u_t1 * u_t2
  quad_u_m <- lam * u_m1 * u_m2
  quad_cross <- lam * (u_t1 * u_m2 + u_m1 * u_t2)

  # Combine: tier + cross-guard + quadratics
  u_t_result <- u_t_tier + cross_linear + quad_u_t + quad_cross
  u_m_result <- u_m_tier + quad_u_m

  obj <- list(
    actual_pair = NUPair(n_a_result, u_t_result),
    measured_pair = NUPair(n_m_result, u_m_result)
  )
  class(obj) <- "UNAlgebra"
  return(obj)
}

#' U/N Multiplication (operator)
#'
#' @export
`*.UNAlgebra` <- function(x, y) {
  if (inherits(y, "UNAlgebra")) {
    return(un_multiply(x, y))
  } else if (is.numeric(y)) {
    # Scalar multiplication
    return(un_scale(x, y))
  }
  stop("Invalid multiplication")
}

#' U/N Scalar Multiplication
#'
#' @param un U/N value
#' @param a Scalar
#'
#' @return Scaled U/N value
#'
#' @export
un_scale <- function(un, a) {
  if (!inherits(un, "UNAlgebra")) {
    stop("First argument must be UNAlgebra")
  }
  
  obj <- list(
    actual_pair = NUPair(a * un$actual_pair$n, abs(a) * un$actual_pair$u),
    measured_pair = NUPair(a * un$measured_pair$n, abs(a) * un$measured_pair$u)
  )
  class(obj) <- "UNAlgebra"
  return(obj)
}

#' U/N Subtraction
#'
#' @export
`-.UNAlgebra` <- function(x, y = NULL) {
  if (is.null(y)) {
    # Negation
    return(un_scale(x, -1))
  }
  # Subtraction
  return(un_add(x, un_scale(y, -1)))
}

# ===== SPECIAL OPERATORS =====

#' Catch Operator
#'
#' Collapse actual tier to zero, absorb into measurement uncertainty.
#'
#' @param un U/N value
#'
#' @return Caught U/N value
#'
#' @export
un_catch <- function(un) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  n_a <- un$actual_pair$n
  u_t <- un$actual_pair$u
  n_m <- un$measured_pair$n
  u_m <- un$measured_pair$u
  
  collapsed_u_m <- abs(n_m - n_a) + u_t + u_m
  
  obj <- list(
    actual_pair = NUPair(0.0, 0.0),
    measured_pair = NUPair(n_m, collapsed_u_m)
  )
  class(obj) <- "UNAlgebra"
  return(obj)
}

#' Flip Operator
#'
#' Swap actual/tolerance with measured/precision (involution).
#'
#' @param un U/N value
#'
#' @return Flipped U/N value
#'
#' @export
un_flip <- function(un) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  obj <- list(
    actual_pair = un$measured_pair,
    measured_pair = un$actual_pair
  )
  class(obj) <- "UNAlgebra"
  return(obj)
}

# ===== INVARIANTS & VALIDATION =====

#' U/N Invariant M
#'
#' M(UN) = |n_a| + u_t + |n_m| + u_m
#'
#' @param un U/N value
#'
#' @return Invariant value (numeric)
#'
#' @export
un_invariant_M <- function(un) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  return(
    abs(un$actual_pair$n) + un$actual_pair$u +
    abs(un$measured_pair$n) + un$measured_pair$u
  )
}

#' Triangle Inequality Check
#'
#' Verify |n_m - n_a| <= u_t + u_m
#'
#' @param un U/N value
#'
#' @return Logical (TRUE if valid)
#'
#' @export
un_triangle_check <- function(un) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  n_a <- un$actual_pair$n
  u_t <- un$actual_pair$u
  n_m <- un$measured_pair$n
  u_m <- un$measured_pair$u
  
  diff <- abs(n_m - n_a)
  bound <- u_t + u_m
  
  return(diff <= bound + 1e-10)
}

#' Triangle Inequality Gap
#'
#' Return how much room in triangle inequality.
#'
#' @param un U/N value
#'
#' @return Gap value (numeric)
#'
#' @export
un_triangle_gap <- function(un) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  n_a <- un$actual_pair$n
  u_t <- un$actual_pair$u
  n_m <- un$measured_pair$n
  u_m <- un$measured_pair$u
  
  diff <- abs(n_m - n_a)
  bound <- u_t + u_m
  
  return(bound - diff)
}

# ===== PROJECTION TO N/U =====

#' Project to N/U
#'
#' Case A (n_a known): π(UN) = (n_m, |n_m - n_a| + u_m)
#' Case B (n_a unknown): π(UN) = (n_m, u_t + u_m)
#'
#' @param un U/N value
#' @param n_a_known Logical (default TRUE)
#'
#' @return N/U pair (NUPair)
#'
#' @export
un_project_to_NU <- function(un, n_a_known = TRUE) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  n_a <- un$actual_pair$n
  u_t <- un$actual_pair$u
  n_m <- un$measured_pair$n
  u_m <- un$measured_pair$u
  
  if (n_a_known) {
    return(NUPair(n_m, abs(n_m - n_a) + u_m))
  } else {
    return(NUPair(n_m, u_t + u_m))
  }
}

# ===== BOUNDS & INTERVALS =====

#' Actual Bounds
#'
#' @param un U/N value
#'
#' @return Vector c(lower, upper)
#'
#' @export
un_actual_bounds <- function(un) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  n <- un$actual_pair$n
  u <- un$actual_pair$u
  
  return(c(n - u, n + u))
}

#' Measured Bounds
#'
#' @param un U/N value
#'
#' @return Vector c(lower, upper)
#'
#' @export
un_measured_bounds <- function(un) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  n <- un$measured_pair$n
  u <- un$measured_pair$u
  
  return(c(n - u, n + u))
}

#' Combined Bounds
#'
#' @param un U/N value
#'
#' @return Vector c(lower, upper)
#'
#' @export
un_combined_bounds <- function(un) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  n_a <- un$actual_pair$n
  u_t <- un$actual_pair$u
  n_m <- un$measured_pair$n
  u_m <- un$measured_pair$u
  
  lower <- min(n_a - u_t, n_m - u_m)
  upper <- max(n_a + u_t, n_m + u_m)
  
  return(c(lower, upper))
}

# ===== COSMOLOGICAL APPLICATION =====

#' Hubble Constant U/N Merge
#'
#' Merge two Hubble measurements with tensor distance weighting.
#'
#' @param early_H0 Early universe U/N measurement
#' @param late_H0 Late universe U/N measurement
#' @param tensor_distance Epistemic distance Δ_T
#'
#' @return Merged U/N value
#'
#' @export
hubble_un_merge <- function(early_H0, late_H0, tensor_distance = 1.0) {
  if (!inherits(early_H0, "UNAlgebra") || !inherits(late_H0, "UNAlgebra")) {
    stop("Both arguments must be UNAlgebra")
  }
  
  n_a_merged <- (early_H0$actual_pair$n + late_H0$actual_pair$n) / 2
  u_t_base <- (early_H0$actual_pair$u + late_H0$actual_pair$u) / 2
  
  n_m_merged <- (early_H0$measured_pair$n + late_H0$measured_pair$n) / 2
  u_m_base <- (early_H0$measured_pair$u + late_H0$measured_pair$u) / 2
  
  disagreement <- abs(early_H0$measured_pair$n - late_H0$measured_pair$n)
  u_t_expanded <- u_t_base + (disagreement / 2) * tensor_distance
  
  return(UNAlgebra(n_a_merged, u_t_expanded, n_m_merged, u_m_base))
}

# ===== UTILITIES =====

#' Convert U/N to List
#'
#' @param un U/N value
#'
#' @return List representation
#'
#' @export
un_to_list <- function(un) {
  if (!inherits(un, "UNAlgebra")) {
    stop("Argument must be UNAlgebra")
  }
  
  return(list(
    n_a = un$actual_pair$n,
    u_t = un$actual_pair$u,
    n_m = un$measured_pair$n,
    u_m = un$measured_pair$u,
    invariant_M = un_invariant_M(un),
    triangle_valid = un_triangle_check(un)
  ))
}

#' Summary of U/N Value
#'
#' @export
summary.UNAlgebra <- function(object, ...) {
  cat("U/N Algebra Element\n")
  cat("==================\n")
  cat(sprintf("Actual (n_a, u_t):   (%.6f, %.6f)\n", 
              object$actual_pair$n, object$actual_pair$u))
  cat(sprintf("Measured (n_m, u_m): (%.6f, %.6f)\n",
              object$measured_pair$n, object$measured_pair$u))
  cat(sprintf("Invariant M:         %.6f\n", un_invariant_M(object)))
  cat(sprintf("Triangle Valid:      %s\n", 
              ifelse(un_triangle_check(object), "Yes", "No")))
  cat(sprintf("Triangle Gap:        %.6f\n", un_triangle_gap(object)))
  invisible(object)
}

# ===== EXAMPLE USAGE =====

if (FALSE) {
  # Create U/N values
  un1 <- UNAlgebra(n_a=10.0, u_t=0.5, n_m=10.1, u_m=0.2)
  un2 <- UNAlgebra(n_a=20.0, u_t=0.3, n_m=19.9, u_m=0.1)
  
  print(un1)
  print(un2)
  
  # Operations
  sum_result <- un1 + un2
  print(sum_result)
  
  prod_result <- un1 * un2
  print(prod_result)
  
  # Special operators
  caught <- un_catch(un1)
  flipped <- un_flip(un1)
  
  # Projection and validation
  proj <- un_project_to_NU(un1)
  summary(un1)
}
