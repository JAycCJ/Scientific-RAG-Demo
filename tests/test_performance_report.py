import tempfile
import unittest
from pathlib import Path

from scripts.report_performance import percentile, summarize_latencies, directory_size


class PerformanceReportTests(unittest.TestCase):
    def test_percentile_interpolates_sorted_values(self):
        self.assertEqual(percentile([1.0, 2.0, 3.0, 4.0], 50), 2.5)
        self.assertEqual(percentile([1.0, 2.0, 3.0, 4.0], 95), 3.85)

    def test_latency_summary_reports_mean_median_and_p95(self):
        result = summarize_latencies([0.1, 0.2, 0.3, 0.4])
        self.assertEqual(result["mean"], 0.25)
        self.assertEqual(result["median"], 0.25)
        self.assertEqual(result["p95"], 0.385)

    def test_directory_size_sums_nested_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.bin").write_bytes(b"123")
            (root / "nested").mkdir()
            (root / "nested" / "b.bin").write_bytes(b"12345")
            self.assertEqual(directory_size(root), 8)


if __name__ == "__main__":
    unittest.main()
