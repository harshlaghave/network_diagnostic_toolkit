"""CSV report export for real diagnostic results."""

import csv
from datetime import datetime, timezone
from pathlib import Path

CSV_HEADERS = ["timestamp", "target", "test", "status", "message", "details"]


def _unique_path(directory: Path, filename: str) -> Path:
    """Return a path inside *directory* that does not overwrite anything.

    If ``filename`` already exists, ``_1``, ``_2`` ... are appended
    before the file extension until a free name is found.
    """
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        numbered = directory / f"{stem}_{counter}{suffix}"
        if not numbered.exists():
            return numbered
        counter += 1


def export_report_to_csv(results, filename=None, reports_dir="reports") -> str:
    """Export *results* to a UTF-8 CSV file and return its path as a string.

    Returns an empty string when there is nothing to export or when
    writing fails (a short message is printed in both cases).
    """
    if not results:
        print("No results to export yet. Run a diagnostic test first.")
        return ""

    directory = Path(reports_dir)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Could not create the reports directory '{directory}': {exc}")
        return ""

    if filename:
        chosen = Path(filename).name  # ignore any directory parts for safety
        if not chosen.lower().endswith(".csv"):
            chosen += ".csv"
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        chosen = f"network_report_{stamp}.csv"

    path = _unique_path(directory, chosen)

    try:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS, extrasaction="ignore")
            writer.writeheader()
            for row in results:
                writer.writerow({key: row.get(key, "") for key in CSV_HEADERS})
    except OSError as exc:
        print(f"Could not write the report file '{path}': {exc}")
        return ""

    print(f"Report saved to {path}")
    return str(path)
