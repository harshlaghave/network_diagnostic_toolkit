"""Tests for CSV report export. Uses temp dirs; no internet access."""

import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from report_generator import CSV_HEADERS, export_report_to_csv


def _sample_results():
    return [
        {
            "timestamp": "2026-01-01T10:00:00+00:00",
            "target": "example.com",
            "test": "DNS",
            "status": "SUCCESS",
            "message": "'example.com' resolved to 93.184.216.34.",
            "details": "93.184.216.34",
        },
        {
            "timestamp": "2026-01-01T10:00:01+00:00",
            "target": "example.com",
            "test": "TCP",
            "status": "FAILED",
            "message": "Connection refused.",
            "details": "port=443",
        },
    ]


class TestReportGenerator(unittest.TestCase):
    def test_export_with_sample_data(self):
        with TemporaryDirectory() as tmp:
            path = export_report_to_csv(_sample_results(), reports_dir=tmp)
            self.assertTrue(path)
            self.assertTrue(Path(path).exists())

    def test_csv_headers_and_row_counts(self):
        with TemporaryDirectory() as tmp:
            rows = _sample_results()
            path = export_report_to_csv(rows, filename="report.csv", reports_dir=tmp)
            with open(path, newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, CSV_HEADERS)
                loaded = list(reader)
            self.assertEqual(len(loaded), len(rows))
            self.assertEqual(loaded[0]["test"], "DNS")
            self.assertEqual(loaded[0]["status"], "SUCCESS")
            self.assertEqual(loaded[1]["test"], "TCP")

    def test_export_with_no_results(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(export_report_to_csv([], reports_dir=tmp), "")
            self.assertEqual(export_report_to_csv(None, reports_dir=tmp), "")
            # Nothing should have been written.
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_does_not_overwrite_existing_report(self):
        with TemporaryDirectory() as tmp:
            first = export_report_to_csv(
                _sample_results(), filename="report.csv", reports_dir=tmp
            )
            second = export_report_to_csv(
                _sample_results(), filename="report.csv", reports_dir=tmp
            )
            self.assertTrue(first)
            self.assertTrue(second)
            self.assertNotEqual(first, second)
            self.assertTrue(Path(first).exists())
            self.assertTrue(Path(second).exists())

    def test_default_filename_pattern(self):
        with TemporaryDirectory() as tmp:
            path = export_report_to_csv(_sample_results(), reports_dir=tmp)
            name = Path(path).name
            self.assertTrue(name.startswith("network_report_"))
            self.assertTrue(name.endswith(".csv"))


if __name__ == "__main__":
    unittest.main()
