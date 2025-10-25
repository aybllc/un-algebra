"""
U/N Algebra Re-Anchoring Visualizers

Plotting utilities for visualizing re-anchoring diagnostics:
- Before/after interval comparison
- Δₜ sensitivity sweeps
- Multiway dataset compass plots
- Tabular diagnostic output

Author: Eric D. Martin
License: CC BY 4.0
Version: 1.0-beta
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, Dict
from .reanchor import UNReanchor


def plot_reanchor_before_after(datasets: List[Tuple[str, float, float]],
                               result: Dict = None,
                               figsize: Tuple[float, float] = (12, 5)) -> plt.Figure:
    """
    Plot intervals before and after re-anchoring.

    Shows:
    - Left panel: Original measurements as intervals
    - Right panel: Re-anchored measurements with shared UNA marked
    - Overlap regions highlighted

    Parameters:
        datasets: List of (name, n, u) tuples (original measurements)
        result: Optional pre-computed reanchor result; if None, computes it
        figsize: Figure size (width, height) in inches

    Returns:
        matplotlib Figure object

    Example:
        >>> planck = ("Planck", 67.3217, 0.3963)
        >>> shoes = ("SH0ES", 72.6744, 0.9029)
        >>> fig = plot_reanchor_before_after([planck, shoes])
        >>> plt.show()
    """
    if result is None:
        reanchor = UNReanchor(datasets)
        result = reanchor.reanchor()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Left panel: BEFORE (original measurements)
    ax1.set_title("Before Re-Anchoring", fontsize=14, fontweight='bold')
    ax1.set_xlabel("Value", fontsize=12)
    ax1.set_ylabel("Dataset", fontsize=12)

    for i, (name, n, u) in enumerate(datasets):
        lower = n - u
        upper = n + u
        ax1.plot([lower, upper], [i, i], 'o-', linewidth=3, markersize=8,
                label=name, color=f"C{i}")
        ax1.axvline(n, ymin=(i-0.2)/len(datasets), ymax=(i+0.2)/len(datasets),
                   linestyle='--', color=f"C{i}", alpha=0.5)

    ax1.set_yticks(range(len(datasets)))
    ax1.set_yticklabels([name for name, _, _ in datasets])
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')

    # Right panel: AFTER (re-anchored)
    ax2.set_title("After Re-Anchoring (Shared UNA)", fontsize=14, fontweight='bold')
    ax2.set_xlabel("Value", fontsize=12)
    ax2.set_ylabel("Dataset", fontsize=12)

    n_anchor, u_t = result['anchor']

    for i, (name, lower, upper) in enumerate(result['intervals']):
        n = result['adjusted'][i][1]  # nominal value
        ax2.plot([lower, upper], [i, i], 'o-', linewidth=3, markersize=8,
                label=name, color=f"C{i}")
        ax2.axvline(n, ymin=(i-0.2)/len(datasets), ymax=(i+0.2)/len(datasets),
                   linestyle='--', color=f"C{i}", alpha=0.5)

    # Mark the shared anchor
    ax2.axvline(n_anchor, color='red', linestyle='--', linewidth=2,
               label=f'Shared UNA = {n_anchor:.3f}', alpha=0.7)

    ax2.set_yticks(range(len(datasets)))
    ax2.set_yticklabels([name for name, _, _ in datasets])
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')

    # Add overlap status annotation
    overlap_text = "✓ OVERLAPPING" if result['overlap'] else "✗ DISJOINT"
    overlap_color = "green" if result['overlap'] else "red"
    ax2.text(0.02, 0.98, overlap_text, transform=ax2.transAxes,
            fontsize=12, fontweight='bold', color=overlap_color,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    return fig


def plot_sensitivity_delta_t(datasets: List[Tuple[str, float, float]],
                             delta_t_range: Tuple[float, float] = (0.0, 3.0),
                             n_points: int = 50,
                             figsize: Tuple[float, float] = (10, 6)) -> plt.Figure:
    """
    Plot merged uncertainty as function of Δₜ.

    Shows how the total merged uncertainty grows with epistemic tensor distance.

    Parameters:
        datasets: List of (name, n, u) tuples
        delta_t_range: (min, max) range for Δₜ sweep
        n_points: Number of points to sample
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object

    Example:
        >>> datasets = [("Planck", 67.3217, 0.3963), ("SH0ES", 72.6744, 0.9029)]
        >>> fig = plot_sensitivity_delta_t(datasets, delta_t_range=(0, 2))
        >>> plt.show()
    """
    reanchor = UNReanchor(datasets)
    reanchor.reanchor()  # Compute adjusted values

    delta_t_values = np.linspace(delta_t_range[0], delta_t_range[1], n_points)
    u_std_values = []
    u_expand_values = []
    u_total_values = []

    for delta_t in delta_t_values:
        merged = reanchor.merge(delta_t=delta_t)
        u_std_values.append(merged['u_std'])
        u_expand_values.append(merged['u_expand'])
        u_total_values.append(merged['u_total'])

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(delta_t_values, u_std_values, 'b--', linewidth=2,
           label='u_std (standard uncertainty)', alpha=0.7)
    ax.plot(delta_t_values, u_expand_values, 'r--', linewidth=2,
           label='u_expand (epistemic expansion)', alpha=0.7)
    ax.plot(delta_t_values, u_total_values, 'g-', linewidth=3,
           label='u_total = u_std + u_expand', alpha=0.9)

    ax.set_xlabel('Epistemic Tensor Distance (Δₜ)', fontsize=12)
    ax.set_ylabel('Uncertainty', fontsize=12)
    ax.set_title('Merged Uncertainty vs. Δₜ', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=10)

    # Mark key points
    ax.axvline(0, color='black', linestyle=':', alpha=0.3)
    ax.text(0.05, 0.95, f'Δₜ=0: Anchor-only\nreconciliation',
           transform=ax.transAxes, fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

    plt.tight_layout()
    return fig


def plot_multiway_compass(datasets: List[Tuple[str, float, float]],
                          result: Dict = None,
                          figsize: Tuple[float, float] = (8, 8)) -> plt.Figure:
    """
    Compass plot showing all datasets relative to shared anchor.

    Each dataset is shown as a vector from the anchor point, with length
    proportional to its distance from the anchor.

    Parameters:
        datasets: List of (name, n, u) tuples
        result: Optional pre-computed reanchor result
        figsize: Figure size (width, height)

    Returns:
        matplotlib Figure object

    Example:
        >>> datasets = [("A", 65, 0.5), ("B", 70, 0.8), ("C", 75, 0.6)]
        >>> fig = plot_multiway_compass(datasets)
        >>> plt.show()
    """
    if result is None:
        reanchor = UNReanchor(datasets)
        result = reanchor.reanchor()

    n_anchor, u_t = result['anchor']

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))

    n_datasets = len(datasets)
    angles = np.linspace(0, 2 * np.pi, n_datasets, endpoint=False)

    for i, ((name, n, u), angle) in enumerate(zip(datasets, angles)):
        distance = abs(n - n_anchor)
        ax.plot([angle, angle], [0, distance], 'o-', linewidth=2,
               markersize=10, label=name, color=f"C{i}")

        # Add uncertainty bar
        u_proj = u_t + result['adjusted'][i][2]
        ax.plot([angle, angle], [distance - u/2, distance + u/2],
               color=f"C{i}", linewidth=4, alpha=0.3)

    # Mark the shared tolerance circle
    theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(theta, [u_t] * len(theta), 'r--', linewidth=2,
           label=f'Shared u_t = {u_t:.3f}', alpha=0.7)

    ax.set_title(f'Multiway Re-Anchoring Compass\n(Anchor at origin: {n_anchor:.3f})',
                fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

    plt.tight_layout()
    return fig


def print_diagnostic_table(result: Dict):
    """
    Print formatted diagnostic table showing re-anchoring results.

    Parameters:
        result: Dictionary returned by UNReanchor.reanchor()

    Example:
        >>> reanchor = UNReanchor([("Planck", 67.3217, 0.3963), ("SH0ES", 72.6744, 0.9029)])
        >>> result = reanchor.reanchor()
        >>> print_diagnostic_table(result)
    """
    print("\n" + "=" * 80)
    print("U/N RE-ANCHORING DIAGNOSTIC TABLE")
    print("=" * 80)

    n_anchor, u_t = result['anchor']
    print(f"\nShared Anchor: n_a^(0) = {n_anchor:.6f}, u_t^(0) = {u_t:.6f}")

    print("\n" + "-" * 80)
    header = f"{'Dataset':<15} {'n':<12} {'u_original':<15} {'u_adjusted':<15} {'Interval':<25}"
    print(header)
    print("-" * 80)

    # Get original uncertainties from first call (assuming datasets available)
    for i, (name, _, _) in enumerate(result['adjusted']):
        n = result['adjusted'][i][1]
        u_prime = result['adjusted'][i][2]
        lower, upper = result['intervals'][i][1], result['intervals'][i][2]

        # For original u, we'd need it passed in; for now show adjusted only
        print(f"{name:<15} {n:<12.4f} {'N/A':<15} {u_prime:<15.4f} "
              f"[{lower:>8.4f}, {upper:>8.4f}]")

    print("-" * 80)

    print(f"\nOverlap Status: {'✓ INTERVALS TOUCH/OVERLAP' if result['overlap'] else '✗ INTERVALS DISJOINT'}")
    print(f"Minimum Gap: {result['gap']:.6f}")

    if result['overlap']:
        print("\n→ Conclusion: Tension is REFERENTIAL (frame artifact)")
        print("  The disagreement vanishes when expressed in a common reference frame.")
    else:
        print("\n→ Conclusion: Tension is PHYSICAL or MODEL-LEVEL")
        print(f"  Intervals remain disjoint by {result['gap']:.4f} even after re-anchoring.")

    print("=" * 80 + "\n")


# Example usage
if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for testing

    # Test with Planck/SH0ES data
    planck = ("Planck", 67.3217, 0.3963)
    shoes = ("SH0ES", 72.6744, 0.9029)
    datasets = [planck, shoes]

    reanchor = UNReanchor(datasets)
    result = reanchor.reanchor()

    print("Generating visualizations...")

    # Test diagnostic table
    print_diagnostic_table(result)

    # Test before/after plot
    fig1 = plot_reanchor_before_after(datasets, result)
    fig1.savefig('/tmp/reanchor_before_after.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: /tmp/reanchor_before_after.png")

    # Test Δₜ sensitivity
    fig2 = plot_sensitivity_delta_t(datasets)
    fig2.savefig('/tmp/reanchor_delta_t.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: /tmp/reanchor_delta_t.png")

    # Test multiway compass (with 3 datasets)
    three_datasets = [("Dataset A", 65.0, 0.5), ("Dataset B", 70.0, 0.8), ("Dataset C", 75.0, 0.6)]
    fig3 = plot_multiway_compass(three_datasets)
    fig3.savefig('/tmp/reanchor_compass.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: /tmp/reanchor_compass.png")

    print("\nAll visualizations generated successfully!")
