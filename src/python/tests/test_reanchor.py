"""
U/N Algebra Re-Anchoring Test Suite

Comprehensive pytest suite for reanchor module:
- Planck/SH0ES Hubble tension case
- Synthetic multiway datasets
- Edge cases and numerical stability
- Merge protocol validation

Author: Eric D. Martin
License: CC BY 4.0
Version: 1.0-beta
"""

import pytest
import math
from un_algebra.reanchor import UNReanchor, reanchor_pairwise, weighted_reanchor


class TestReanchorPlanckSHOES:
    """Tests using real Planck and SH0ES Hubble constant measurements."""

    def test_planck_shoes_overlap(self):
        """Test that Planck and SH0ES intervals touch after re-anchoring."""
        planck = ("Planck", 67.3217, 0.3963)
        shoes = ("SH0ES", 72.6744, 0.9029)

        reanchor = UNReanchor([planck, shoes])
        result = reanchor.reanchor()

        # Verify overlap
        assert result['overlap'], "Planck and SH0ES should overlap after re-anchoring"
        assert result['gap'] < 1e-10, f"Gap should be ~0, got {result['gap']}"

    def test_planck_shoes_anchor_midpoint(self):
        """Test that anchor is at midpoint for unweighted case."""
        planck = ("Planck", 67.3217, 0.3963)
        shoes = ("SH0ES", 72.6744, 0.9029)

        reanchor = UNReanchor([planck, shoes])
        result = reanchor.reanchor()

        expected_anchor = (67.3217 + 72.6744) / 2
        assert abs(result['anchor'][0] - expected_anchor) < 1e-6

    def test_planck_shoes_adjusted_uncertainties(self):
        """Test that adjusted uncertainties satisfy triangle inequality."""
        planck = ("Planck", 67.3217, 0.3963)
        shoes = ("SH0ES", 72.6744, 0.9029)

        reanchor = UNReanchor([planck, shoes])
        result = reanchor.reanchor()

        n_anchor, u_t = result['anchor']

        for name, n, u_prime in result['adjusted']:
            d = abs(n - n_anchor)
            # Triangle inequality: |n - n_anchor| ≤ u_t + u'
            assert d <= u_t + u_prime + 1e-10, \
                f"{name}: Triangle inequality violated: {d} > {u_t + u_prime}"

    def test_planck_shoes_interval_meeting(self):
        """Test that intervals meet exactly at the anchor point."""
        planck = ("Planck", 67.3217, 0.3963)
        shoes = ("SH0ES", 72.6744, 0.9029)

        reanchor = UNReanchor([planck, shoes])
        result = reanchor.reanchor()

        n_anchor = result['anchor'][0]

        # Get intervals
        _, lower1, upper1 = result['intervals'][0]
        _, lower2, upper2 = result['intervals'][1]

        # Check that one upper bound equals the anchor (or very close)
        assert (abs(upper1 - n_anchor) < 1e-6) or (abs(upper2 - n_anchor) < 1e-6), \
            f"Expected interval to meet at anchor {n_anchor:.6f}"

    def test_planck_shoes_symmetry(self):
        """Test that order of datasets doesn't affect result."""
        planck = ("Planck", 67.3217, 0.3963)
        shoes = ("SH0ES", 72.6744, 0.9029)

        result1 = UNReanchor([planck, shoes]).reanchor()
        result2 = UNReanchor([shoes, planck]).reanchor()

        assert abs(result1['anchor'][0] - result2['anchor'][0]) < 1e-10
        assert result1['overlap'] == result2['overlap']


class TestReanchorSynthetic:
    """Tests using synthetic datasets with known properties."""

    def test_identical_measurements(self):
        """Test that identical measurements have zero adjusted uncertainty."""
        dataset = [("A", 70.0, 0.5), ("B", 70.0, 0.5)]

        reanchor = UNReanchor(dataset)
        result = reanchor.reanchor()

        # All measurements at anchor, no adjustment needed
        assert result['overlap'], "Identical measurements should overlap"
        assert result['gap'] == 0.0

    def test_already_compatible(self):
        """Test measurements that already overlap without adjustment."""
        # Two measurements with overlapping intervals
        dataset = [("A", 68.0, 2.0), ("B", 70.0, 2.0)]

        reanchor = UNReanchor(dataset)
        result = reanchor.reanchor()

        assert result['overlap'], "Compatible measurements should overlap"

    def test_disjoint_large_gap(self):
        """Test that large gaps are correctly detected."""
        # Measurements with large separation
        dataset = [("A", 50.0, 0.1), ("B", 100.0, 0.1)]

        reanchor = UNReanchor(dataset)
        result = reanchor.reanchor()

        # After minimal adjustment, they should touch
        assert result['overlap'], "Re-anchoring should close gaps via adjustment"

    def test_three_datasets_multiway(self):
        """Test multiway re-anchoring with 3 datasets."""
        datasets = [
            ("A", 65.0, 0.5),
            ("B", 70.0, 0.8),
            ("C", 75.0, 0.6)
        ]

        reanchor = UNReanchor(datasets)
        result = reanchor.reanchor()

        # Verify all satisfy triangle inequality
        n_anchor, u_t = result['anchor']
        for name, n, u_prime in result['adjusted']:
            d = abs(n - n_anchor)
            assert d <= u_t + u_prime + 1e-10, \
                f"{name}: Triangle inequality violated"

        # Verify anchor is at centroid
        expected_anchor = (65.0 + 70.0 + 75.0) / 3
        assert abs(result['anchor'][0] - expected_anchor) < 1e-6


class TestWeightedReanchoring:
    """Tests for weighted (inverse-variance) re-anchoring."""

    def test_weighted_anchor_location(self):
        """Test that weighted anchor favors more precise measurements."""
        # Precise measurement at 68, imprecise at 72
        datasets = [("Precise", 68.0, 0.1), ("Imprecise", 72.0, 2.0)]

        result = weighted_reanchor(datasets, use_inverse_variance=True)

        # Anchor should be closer to the precise measurement
        n_anchor = result['anchor'][0]
        assert n_anchor < 70.0, f"Weighted anchor should favor precise measurement: {n_anchor:.3f}"

    def test_equal_weights_equals_unweighted(self):
        """Test that uniform weights equal unweighted reanchoring."""
        datasets = [("A", 67.0, 0.5), ("B", 73.0, 0.8)]

        result_weighted = weighted_reanchor(datasets, use_inverse_variance=False)
        result_unweighted = UNReanchor(datasets).reanchor()

        assert abs(result_weighted['anchor'][0] - result_unweighted['anchor'][0]) < 1e-10


class TestMergeProtocol:
    """Tests for merge() method with Δₜ epistemic expansion."""

    def test_merge_delta_t_zero(self):
        """Test that Δₜ=0 gives anchor-only reconciliation."""
        datasets = [("A", 67.0, 0.4), ("B", 73.0, 0.9)]

        reanchor = UNReanchor(datasets)
        reanchor.reanchor()
        merged = reanchor.merge(delta_t=0.0)

        assert merged['u_expand'] == 0.0, "Δₜ=0 should have zero epistemic expansion"
        assert merged['u_total'] == merged['u_std']

    def test_merge_delta_t_positive(self):
        """Test that Δₜ>0 increases merged uncertainty."""
        datasets = [("A", 67.0, 0.4), ("B", 73.0, 0.9)]

        reanchor = UNReanchor(datasets)
        reanchor.reanchor()

        merged0 = reanchor.merge(delta_t=0.0)
        merged1 = reanchor.merge(delta_t=1.0)
        merged2 = reanchor.merge(delta_t=2.0)

        # Uncertainty should increase with Δₜ
        assert merged1['u_total'] > merged0['u_total']
        assert merged2['u_total'] > merged1['u_total']

    def test_merge_disagreement_scaling(self):
        """Test that epistemic expansion scales with disagreement."""
        # Large disagreement
        large = [("A", 60.0, 0.5), ("B", 80.0, 0.5)]
        reanchor_large = UNReanchor(large)
        reanchor_large.reanchor()
        merged_large = reanchor_large.merge(delta_t=1.0)

        # Small disagreement
        small = [("A", 69.0, 0.5), ("B", 71.0, 0.5)]
        reanchor_small = UNReanchor(small)
        reanchor_small.reanchor()
        merged_small = reanchor_small.merge(delta_t=1.0)

        # Large disagreement should have larger epistemic expansion
        assert merged_large['u_expand'] > merged_small['u_expand']


class TestEdgeCases:
    """Tests for edge cases and numerical stability."""

    def test_single_dataset(self):
        """Test that single dataset has no adjustment needed."""
        dataset = [("Single", 70.0, 0.5)]

        reanchor = UNReanchor(dataset)
        result = reanchor.reanchor()

        # Anchor at the single measurement
        assert abs(result['anchor'][0] - 70.0) < 1e-10
        assert result['overlap'], "Single dataset should trivially overlap"

    def test_zero_uncertainty(self):
        """Test handling of zero uncertainty (exact measurement)."""
        datasets = [("Exact", 70.0, 0.0), ("Uncertain", 72.0, 1.0)]

        reanchor = UNReanchor(datasets)
        result = reanchor.reanchor()

        # Should not raise error
        assert result is not None
        assert result['anchor'][1] == 1.0, "u_t should be max(0, 1) = 1"

    def test_negative_uncertainty_raises(self):
        """Test that negative uncertainty raises ValueError."""
        with pytest.raises(ValueError, match="must be non-negative"):
            UNReanchor([("Bad", 70.0, -0.5)])

    def test_empty_datasets_raises(self):
        """Test that empty dataset list raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            UNReanchor([])

    def test_numerical_stability_large_numbers(self):
        """Test stability with large nominal values."""
        datasets = [("A", 1e10, 1e6), ("B", 1e10 + 1e7, 2e6)]

        reanchor = UNReanchor(datasets)
        result = reanchor.reanchor()

        assert result['overlap'], "Should handle large numbers correctly"

    def test_numerical_stability_small_uncertainties(self):
        """Test stability with very small uncertainties."""
        datasets = [("A", 70.0, 1e-10), ("B", 70.0 + 1e-8, 1e-10)]

        reanchor = UNReanchor(datasets)
        result = reanchor.reanchor()

        # Should not have numerical issues
        assert result is not None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_reanchor_pairwise(self):
        """Test pairwise convenience function."""
        result = reanchor_pairwise(67.0, 0.4, 73.0, 0.9)

        assert 'anchor' in result
        assert 'overlap' in result
        assert len(result['adjusted']) == 2

    def test_reanchor_pairwise_matches_class(self):
        """Test that pairwise function matches class method."""
        n1, u1 = 67.0, 0.4
        n2, u2 = 73.0, 0.9

        result_func = reanchor_pairwise(n1, u1, n2, u2)

        reanchor_class = UNReanchor([("A", n1, u1), ("B", n2, u2)])
        result_class = reanchor_class.reanchor()

        assert abs(result_func['anchor'][0] - result_class['anchor'][0]) < 1e-10


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
