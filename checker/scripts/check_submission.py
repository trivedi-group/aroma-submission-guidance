"""Check a laboratory submission folder before it is sent to the AROMA database.

    python scripts/check_submission.py submissions/LU/20270209_B01
    python scripts/check_submission.py "Submission v1 LU.xlsx" -lab LU

The lab code is taken from the first folder name under submissions/ unless -lab is given.
Exit status is 0 when there are no errors. Nothing is written or changed.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aromalib  # noqa: E402


def lab_from_path(path):
    parts = Path(path).resolve().parts
    if "submissions" in parts:
        i = parts.index("submissions")
        if i + 1 < len(parts):
            return parts[i + 1]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder")
    parser.add_argument("-lab", help="lab code, for example LU")
    parser.add_argument("-standards", help="folder with standards.csv and standard_components.csv, default is registry/standards")
    args = parser.parse_args()
    lab = args.lab or lab_from_path(args.folder)
    if lab and lab not in aromalib.vocab_codes("labs"):
        print(f"ERROR  lab code {lab} is not in registry/vocab/labs.csv")
        return 1
    folder = args.folder
    if folder.lower().endswith(".xlsx"):
        import tempfile
        import xlsx_to_csv
        folder = tempfile.mkdtemp(prefix="aroma_xlsx_")
        xlsx_to_csv.convert(args.folder, folder)
    report, _ = aromalib.check_submission(folder, lab, args.standards)
    text = report.render()
    if text:
        print(text)
    print("PASS" if report.ok() else f"FAIL  {len(report.errors)} error groups")
    return 0 if report.ok() else 1


if __name__ == "__main__":
    sys.exit(main())
