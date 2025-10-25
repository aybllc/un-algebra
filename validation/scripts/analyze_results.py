#!/usr/bin/env python3
"""
U/N Algebra Phase 3 Results Analysis
Parses test output, calculates PAC confidence, generates publication-ready tables
"""

import re
import json
import math
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class ResultsAnalyzer:
    """Analyze Phase 3 test results."""

    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.results = {
            'timestamp': None,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'success_rate': 0.0,
            'runtime_seconds': 0.0,
            'categories': {},
            'pac_confidence': {}
        }

    def parse_log(self):
        """Extract test results from log file."""
        with open(self.log_file, 'r') as f:
            content = f.read()

        # Extract summary statistics
        total_match = re.search(r'Total Tests: (\d+)', content)
        passed_match = re.search(r'Passed: (\d+)', content)
        failed_match = re.search(r'Failed: (\d+)', content)
        time_match = re.search(r'Time Elapsed: ([\d.]+)s', content)

        if total_match:
            self.results['total_tests'] = int(total_match.group(1))
        if passed_match:
            self.results['passed'] = int(passed_match.group(1))
        if failed_match:
            self.results['failed'] = int(failed_match.group(1))
        if time_match:
            self.results['runtime_seconds'] = float(time_match.group(1))

        if self.results['total_tests'] > 0:
            self.results['success_rate'] = 100 * self.results['passed'] / self.results['total_tests']

        # Extract by-category results
        category_pattern = r'(\w+)\s+:\s+(\d+)/\s*(\d+)\s+\(([\d.]+)%\)'
        for match in re.finditer(category_pattern, content):
            category = match.group(1)
            passed = int(match.group(2))
            total = int(match.group(3))
            rate = float(match.group(4))

            self.results['categories'][category] = {
                'passed': passed,
                'total': total,
                'failed': total - passed,
                'success_rate': rate
            }

    def calculate_pac_confidence(self):
        """Calculate PAC confidence bounds using Chernoff inequality."""
        n = self.results['total_tests']
        failures = self.results['failed']

        if n == 0:
            return

        # Chernoff bound: P(error_rate > ε) < exp(-n * ε^2 / 2)
        epsilons = [0.0001, 0.001, 0.01, 0.05]

        for eps in epsilons:
            if failures == 0:
                # Theoretical bound when no failures observed
                confidence_bound = math.exp(-n * eps**2 / 2)

                # Convert to scientific notation
                if confidence_bound < 1e-10:
                    exponent = int(math.floor(math.log10(confidence_bound)))
                    mantissa = confidence_bound / (10 ** exponent)
                    bound_str = f"{mantissa:.2f}e{exponent}"
                else:
                    bound_str = f"{confidence_bound:.10f}"

                self.results['pac_confidence'][f'epsilon_{eps}'] = {
                    'epsilon': eps,
                    'probability_bound': bound_str,
                    'interpretation': f"P(true_error > {eps}) < {bound_str}"
                }
            else:
                # Empirical error rate
                empirical_rate = failures / n
                self.results['pac_confidence'][f'epsilon_{eps}'] = {
                    'epsilon': eps,
                    'empirical_error_rate': empirical_rate,
                    'comparison': 'above' if empirical_rate > eps else 'below'
                }

    def generate_summary_json(self, output_file: str):
        """Save results as JSON."""
        self.results['timestamp'] = datetime.now().isoformat()

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"✓ Summary JSON saved: {output_file}")

    def generate_markdown_table(self) -> str:
        """Generate markdown table for publication."""
        md = "## Test Results Summary\n\n"
        md += f"**Total Tests**: {self.results['total_tests']:,}\n"
        md += f"**Passed**: {self.results['passed']:,} ✓\n"
        md += f"**Failed**: {self.results['failed']:,}\n"
        md += f"**Success Rate**: {self.results['success_rate']:.2f}%\n"
        md += f"**Runtime**: {self.results['runtime_seconds']:.1f}s\n\n"

        md += "### By Category\n\n"
        md += "| Category | Passed | Total | Success Rate |\n"
        md += "|----------|--------|-------|-------------|\n"

        for cat, stats in sorted(self.results['categories'].items()):
            md += f"| {cat:15s} | {stats['passed']:6,d} | {stats['total']:6,d} | {stats['success_rate']:5.1f}% |\n"

        md += "\n### PAC Confidence Bounds\n\n"
        if self.results['failed'] == 0:
            md += "**Zero failures detected** - Using Chernoff bounds:\n\n"
            md += "| ε (Error Rate) | Upper Bound | Interpretation |\n"
            md += "|----------------|-------------|----------------|\n"

            for key, conf in self.results['pac_confidence'].items():
                md += f"| {conf['epsilon']:.4f} | {conf['probability_bound']} | {conf['interpretation']} |\n"
        else:
            md += f"**Empirical failures**: {self.results['failed']}/{self.results['total_tests']}\n"

        return md

    def print_report(self):
        """Print analysis to console."""
        print("\n" + "=" * 60)
        print("PHASE 3 VALIDATION ANALYSIS")
        print("=" * 60)

        print(f"\nTotal Tests: {self.results['total_tests']:,}")
        print(f"Passed: {self.results['passed']:,} ✓")
        print(f"Failed: {self.results['failed']:,}")
        print(f"Success Rate: {self.results['success_rate']:.2f}%")
        print(f"Runtime: {self.results['runtime_seconds']:.1f}s")

        if self.results['failed'] == 0:
            print("\n🎉 ZERO FAILURES - Framework is robust!")
            print("\nPAC Confidence Bounds (Chernoff):")
            for key, conf in self.results['pac_confidence'].items():
                print(f"  {conf['interpretation']}")
        else:
            print(f"\n⚠️  {self.results['failed']} failures detected - review log file")


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 analyze_results.py <log_file>")
        sys.exit(1)

    log_file = sys.argv[1]

    analyzer = ResultsAnalyzer(log_file)
    analyzer.parse_log()
    analyzer.calculate_pac_confidence()

    # Output files
    base_path = Path(log_file).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary_json = base_path / f"summary_{timestamp}.json"
    markdown_file = base_path / f"results_{timestamp}.md"

    # Generate outputs
    analyzer.generate_summary_json(str(summary_json))

    markdown = analyzer.generate_markdown_table()
    with open(markdown_file, 'w') as f:
        f.write(markdown)
    print(f"✓ Markdown table saved: {markdown_file}")

    # Print to console
    analyzer.print_report()


if __name__ == "__main__":
    main()
