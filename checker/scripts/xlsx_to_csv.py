"""Convert a filled submission workbook into the CSV tables the checker and the build read.

    python scripts/xlsx_to_csv.py "Submission v1 LU.xlsx" submissions/LU/20270209_B01

One CSV is written per sheet that holds data rows. Sheets with only a header row are skipped.
Cells are written exactly as typed. Dates typed as real Excel dates become YYYY-MM-DD. Date and
time values must carry a UTC offset, so type them as text, for example 2027-02-09T10:15:00+00:00.
"""
import csv
import datetime as dt
import sys
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aromalib  # noqa: E402


def cell_text(value, col_type):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Y" if value else "N"
    if isinstance(value, dt.datetime):
        if col_type == "date" and value.time() == dt.time(0):
            return value.date().isoformat()
        return value.isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() and col_type == "int" else format(value, ".15g")
    return str(value).strip()


def convert(xlsx, outdir):
    """Write CSVs to outdir. Returns the list of table names written."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    wb = load_workbook(xlsx, read_only=True, data_only=True)
    written = []
    for name, spec in aromalib.TABLES.items():
        if spec["where"] != "lab" or name not in wb.sheetnames:
            continue
        cols = aromalib.column_names(name)
        types = {c["name"]: c["type"] for c in spec["columns"]}
        rows = wb[name].iter_rows(values_only=True)
        header = [str(h).strip() if h is not None else "" for h in next(rows, [])]
        header = header[: len(cols)] if header[: len(cols)] == cols else [h for h in header if h]
        body = []
        for row in rows:
            values = [cell_text(v, types.get(h)) for h, v in zip(header, row)]
            if any(values):
                body.append(values)
        if body:
            with (outdir / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                writer.writerows(body)
            written.append(name)
    return written


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    written = convert(sys.argv[1], sys.argv[2])
    print("Wrote " + ", ".join(written) if written else "No data rows found")


if __name__ == "__main__":
    main()
