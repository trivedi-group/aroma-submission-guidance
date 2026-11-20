# AROMA submission checker

Checks a filled workbook or a folder of CSV sheets before it is submitted. The checker only reads files and changes nothing.

## Procedure

1. Install Python 3.10 or later.
2. Install the packages with `pip install duckdb openpyxl`.
3. Open a terminal in this folder.
4. Run `python scripts/check_submission.py "my workbook.xlsx" -lab LU`. Replace the file name and the laboratory code.
5. Read the output. Each line names the sheet, the column, the problem and the rows affected. The last line is PASS when there are no errors.
6. Correct every error in the workbook and run the checker again.

## Test with the example

Run `python scripts/check_submission.py "../templates/Example filled workbook v1.xlsx" -lab LU -standards ../example/standards`. The output ends with PASS.

## Notes

- The checker reads the allowed codes, the identifier blocks, the compound list and the standards from this repository. Use the current version of the repository for every check.
- A folder of CSV sheets can be checked in place of a workbook. Give the folder path in place of the file name.
- The standards are read from registry/standards unless -standards names another folder.
