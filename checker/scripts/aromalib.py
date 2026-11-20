"""Shared code for the AROMA submission checker, the database builder and the template generator.

Everything is driven by schema/submission_tables.json and the vocabulary files in registry/vocab,
so adding a laboratory, platform, matrix, adduct or file type is a one-line change to a CSV and
needs no code change. All checks are set-based SQL run by DuckDB, so cost grows with the number
of rows, not with the number of laboratories or compounds.
"""
import csv
import json
import os
from pathlib import Path

import duckdb

ROOT = Path(os.environ.get("AROMA_ROOT") or Path(__file__).resolve().parent.parent)
SPEC = json.loads((ROOT / "schema" / "submission_tables.json").read_text(encoding="utf-8"))
TABLES = SPEC["tables"]
VOCAB_DIR = ROOT / "registry" / "vocab"

REGEX = {
    "date": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
    "datetime": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]+)?)?(Z|[+-][0-9]{2}:[0-9]{2})$",
    "int": r"^-?[0-9]+$",
    "bool": r"^[YN]$",
}
MAX_SHOWN = 5


def q(name):
    return '"' + name.replace('"', '""') + '"'


def lit(text):
    return "'" + str(text).replace("'", "''") + "'"


def vocab_codes(name):
    """Return the list of allowed codes for a vocabulary."""
    if name == "file_kinds_kind":
        path, col = VOCAB_DIR / "file_kinds.csv", "kind"
    else:
        path, col = VOCAB_DIR / f"{name}.csv", "code"
    with path.open(newline="", encoding="utf-8") as handle:
        return sorted({row[col] for row in csv.DictReader(handle)})


def file_kind_extensions():
    with (VOCAB_DIR / "file_kinds.csv").open(newline="", encoding="utf-8") as handle:
        return [(r["kind"], r["extension"]) for r in csv.DictReader(handle)]


def column_names(table):
    return [c["name"] for c in TABLES[table]["columns"]]


def read_header(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return next(csv.reader(handle), [])


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, table, where, message):
        self.errors.append((table, where, message))

    def warn(self, table, where, message):
        self.warnings.append((table, where, message))

    def ok(self):
        return not self.errors

    def render(self):
        lines = []
        for kind, items in (("ERROR", self.errors), ("WARNING", self.warnings)):
            for table, where, message in items:
                lines.append(f"{kind}  {table}  {where}  {message}")
        return "\n".join(lines)


def load_table(con, table, path, report, optional=False, label=None):
    """Load one CSV into DuckDB as all-text, after checking its header. Returns True if loaded."""
    label = label or table
    spec_cols = column_names(table)
    path = Path(path) if path else None
    if path is None or not path.exists():
        if not optional:
            report.error(label, "file", f"missing required table file {table}.csv")
        con.execute(f"CREATE OR REPLACE TABLE {q(table)} (_row BIGINT, " +
                    ", ".join(f"{q(c)} VARCHAR" for c in spec_cols) + ")")
        return False
    header = read_header(path)
    missing = [c for c in spec_cols if c not in header]
    extra = [c for c in header if c not in spec_cols]
    if missing:
        report.error(label, "header", "missing columns: " + ", ".join(missing))
    if extra:
        report.error(label, "header", "unknown columns: " + ", ".join(extra))
    if missing or extra:
        con.execute(f"CREATE OR REPLACE TABLE {q(table)} (_row BIGINT, " +
                    ", ".join(f"{q(c)} VARCHAR" for c in spec_cols) + ")")
        return False
    cols = ", ".join(f"{q(c)}: 'VARCHAR'" for c in header)
    con.execute(
        f"CREATE OR REPLACE TABLE {q(table)} AS SELECT row_number() OVER () + 1 AS _row, " +
        ", ".join(q(c) for c in spec_cols) +
        f" FROM read_csv({lit(str(path))}, header=true, columns={{{cols}}}, nullstr='', "
        "all_varchar=true, strict_mode=false, ignore_errors=false)")
    return True


def load_compounds(con):
    con.execute(
        f"CREATE OR REPLACE TABLE id_blocks AS SELECT * FROM read_csv({lit(str(ROOT / 'registry' / 'id_blocks.csv'))}, "
        "header=true, all_varchar=true, nullstr='')")
    con.execute(
        f"CREATE OR REPLACE TABLE compounds AS SELECT * FROM read_csv({lit(str(ROOT / 'registry' / 'compounds.csv'))}, "
        "header=true, all_varchar=true, nullstr='')")


def _blank(col):
    return f"({q(col)} IS NULL OR trim({q(col)}) = '')"


def _prefix(col):
    return f"substr({q(col)}, 1, 3)"


def _fail(con, report, table, label, column, message, where_sql, extra_cols=""):
    """Record one grouped error for rows of `table` matching where_sql."""
    count = con.execute(f"SELECT count(*) FROM {q(table)} WHERE {where_sql}").fetchone()[0]
    if not count:
        return
    cols = f", {extra_cols}" if extra_cols else ""
    rows = con.execute(
        f"SELECT _row, {q(column) if column else 'NULL'}{cols} FROM {q(table)} WHERE {where_sql} ORDER BY _row LIMIT {MAX_SHOWN}"
    ).fetchall()
    shown = "; ".join(f"line {r[0]}" + (f" value {r[1]!r}" if r[1] is not None else "") for r in rows)
    more = f" and {count - len(rows)} more" if count > len(rows) else ""
    report.error(label, column or "row", f"{message} ({count} rows: {shown}{more})")


def check_columns(con, table, report, label=None):
    """Column level checks from the table specification."""
    label = label or table
    spec = TABLES[table]
    has_sample = "sample_id" in column_names(table)
    for col in spec["columns"]:
        name = col["name"]
        c = q(name)
        present = f"NOT {_blank(name)}"
        required_cond = None
        if col.get("required"):
            required_cond = "TRUE"
            if col.get("required_unless_type") and has_sample:
                prefixes = ", ".join(lit(p) for p in col["required_unless_type"])
                required_cond = f"{_prefix('sample_id')} NOT IN ({prefixes})"
        elif col.get("required_if_type") and has_sample:
            prefixes = ", ".join(lit(p) for p in col["required_if_type"])
            required_cond = f"{_prefix('sample_id')} IN ({prefixes})"
        if required_cond:
            _fail(con, report, table, label, name, "required value is blank", f"{_blank(name)} AND {required_cond}")
        base = present
        t = col["type"]
        if t in REGEX:
            _fail(con, report, table, label, name, f"not a valid {t}", f"{base} AND NOT regexp_matches({c}, {lit(REGEX[t])})")
            if t == "date":
                _fail(con, report, table, label, name, "not a real calendar date",
                      f"{base} AND regexp_matches({c}, {lit(REGEX['date'])}) AND TRY_CAST({c} AS DATE) IS NULL")
        elif t == "number":
            _fail(con, report, table, label, name, "not a finite number",
                  f"{base} AND (TRY_CAST({c} AS DOUBLE) IS NULL OR NOT isfinite(TRY_CAST({c} AS DOUBLE)))")
        if t in ("number", "int"):
            num = f"TRY_CAST({c} AS DOUBLE)"
            if "min" in col:
                _fail(con, report, table, label, name, f"below minimum {col['min']}", f"{base} AND {num} < {col['min']}")
            if "max" in col:
                _fail(con, report, table, label, name, f"above maximum {col['max']}", f"{base} AND {num} > {col['max']}")
            if "min_exclusive" in col:
                _fail(con, report, table, label, name, f"not above {col['min_exclusive']}", f"{base} AND {num} <= {col['min_exclusive']}")
        if "pattern" in col:
            _fail(con, report, table, label, name, "does not match the required pattern " + col["pattern"],
                  f"{base} AND NOT regexp_matches({c}, {lit(col['pattern'])})")
        if "vocab" in col:
            codes = ", ".join(lit(x) for x in vocab_codes(col["vocab"]))
            _fail(con, report, table, label, name, f"not in vocabulary {col['vocab']}", f"{base} AND {c} NOT IN ({codes})")
    key = ", ".join(q(k) for k in spec["key"])
    dup = con.execute(
        f"SELECT count(*) FROM (SELECT {key} FROM {q(table)} GROUP BY {key} HAVING count(*) > 1)").fetchone()[0]
    if dup:
        sample = con.execute(
            f"SELECT {key} FROM {q(table)} GROUP BY {key} HAVING count(*) > 1 LIMIT {MAX_SHOWN}").fetchall()
        report.error(label, "key", f"{dup} duplicate keys on ({', '.join(spec['key'])}), for example {sample}")


def check_foreign_keys(con, table, report, label=None):
    label = label or table
    for fk in TABLES[table].get("foreign_keys", []):
        cols, ref, refcols = fk["columns"], fk["ref_table"], fk["ref_columns"]
        present = " AND ".join(f"NOT {_blank(c)}" for c in cols)
        cond = " AND ".join(f"r.{q(rc)} = t.{q(c)}" for c, rc in zip(cols, refcols))
        where = f"{present} AND NOT EXISTS (SELECT 1 FROM {q(ref)} r WHERE {cond})"
        count = con.execute(f"SELECT count(*) FROM {q(table)} t WHERE {where}").fetchone()[0]
        if count:
            rows = con.execute(
                f"SELECT t._row, {', '.join('t.' + q(c) for c in cols)} FROM {q(table)} t WHERE {where} ORDER BY t._row LIMIT {MAX_SHOWN}"
            ).fetchall()
            shown = "; ".join(f"line {r[0]} {r[1:]}" for r in rows)
            report.error(label, ",".join(cols), f"no matching {ref} ({', '.join(refcols)}) for {count} rows: {shown}")


def cross_checks(con, report, lab=None):
    """Rules that span tables. Each is one set-based query."""
    L = "run_manifest"
    # sample_type must agree with the prefix, and standards must exist in the registry
    _fail(con, report, "sample_manifest", "sample_manifest", "sample_type", "sample_type does not match the sample_id prefix",
          f"NOT {_blank('sample_id')} AND sample_type IS NOT NULL AND sample_type <> {_prefix('sample_id')}")
    _fail(con, report, "sample_manifest", "sample_manifest", "sample_id", "STD sample is not in the UoM standards registry",
          f"{_prefix('sample_id')} = 'STD' AND sample_id NOT IN (SELECT std_id FROM standards)")
    _fail(con, report, "sample_manifest", "sample_manifest", "matrix_code", "standards must have matrix_code neat",
          f"{_prefix('sample_id')} = 'STD' AND matrix_code <> 'neat'")
    _fail(con, report, "sample_manifest", "sample_manifest", "matrix_code", "spiked and real samples must not have matrix_code neat",
          f"{_prefix('sample_id')} <> 'STD' AND matrix_code = 'neat'")
    _fail(con, report, "sample_manifest", "sample_manifest", "sample_id", "sample_id is outside every allocated block in registry/id_blocks.csv",
          f"regexp_matches(sample_id, '^(STD|SPK|BLK|QCP|SMP)[0-9]{{7}}$') AND NOT EXISTS (SELECT 1 FROM id_blocks b WHERE b.sample_type = {_prefix('sample_id')} "
          "AND TRY_CAST(substr(sample_id, 4) AS BIGINT) BETWEEN CAST(b.first AS BIGINT) AND CAST(b.last AS BIGINT))")
    if lab:
        _fail(con, report, "sample_manifest", "sample_manifest", "holding_lab", f"holding_lab is not the submitting lab {lab}",
              f"holding_lab <> {lit(lab)}")
        _fail(con, report, L, L, "lab", f"lab is not the submitting lab {lab}", f"lab <> {lit(lab)}")
    # run_id must agree with the fields it encodes
    parts = "string_split(run_id, '_')"
    for expr, name, text in (
        (f"{parts}[1] <> lab", "lab", "lab in run_id differs from the lab column"),
        (f"{parts}[2] <> platform", "platform", "platform in run_id differs from the platform column"),
        (f"{parts}[3] <> strftime(TRY_CAST(run_date AS DATE), '%Y%m%d')", "run_date", "date in run_id differs from run_date"),
        (f"{parts}[4] <> sample_id || '-' || aliquot", "sample_id", "sample and aliquot in run_id differ from the sample columns"),
        (f"{parts}[5] <> 'R' || lpad(replicate, 2, '0')", "replicate", "replicate in run_id differs from the replicate column"),
        (f"TRY_CAST({parts}[6] AS INTEGER) <> TRY_CAST(run_no AS INTEGER)", "run_no", "run number in run_id differs from run_no"),
    ):
        _fail(con, report, L, L, name, text, f"NOT {_blank('run_id')} AND regexp_matches(run_id, {lit(TABLES[L]['columns'][0]['pattern'])}) AND ({expr})")
    _fail(con, report, L, L, "run_type", "run_type does not agree with the sample prefix",
          "("
          f"(run_type = 'std' AND {_prefix('sample_id')} <> 'STD') OR (run_type = 'spiked' AND {_prefix('sample_id')} <> 'SPK') OR "
          f"(run_type = 'blank' AND {_prefix('sample_id')} <> 'BLK') OR (run_type = 'qc' AND {_prefix('sample_id')} <> 'QCP') OR "
          f"(run_type = 'sample' AND {_prefix('sample_id')} <> 'SMP'))")
    _fail(con, report, L, L, "delivered_volume_ul", "delivered_volume_ul is required for standard and spiked runs",
          f"{_blank('delivered_volume_ul')} AND run_type IN ('std', 'spiked')")
    # the run's lab must hold the aliquot
    _fail(con, report, L, L, "sample_id", "run's lab is not the holding_lab of that aliquot",
          "EXISTS (SELECT 1 FROM sample_manifest s WHERE s.sample_id = run_manifest.sample_id AND s.aliquot = run_manifest.aliquot AND s.holding_lab <> run_manifest.lab)")
    # files
    F = "file_manifest"
    kinds = {}
    for kind, ext in file_kind_extensions():
        kinds.setdefault(kind, []).append(ext)
    _fail(con, report, F, F, "run_id", "run_id is required for raw_vendor and mzml files",
          f"{_blank('run_id')} AND kind IN ('raw_vendor', 'mzml')")
    for kind, exts in kinds.items():
        ok = " OR ".join(f"file_name LIKE {lit('%.' + e)}" for e in exts)
        _fail(con, report, F, F, "file_name", f"file extension is not allowed for kind {kind}",
              f"kind = {lit(kind)} AND NOT ({ok})")
    _fail(con, report, F, F, "file_name", "file name does not begin with its run_id",
          f"NOT {_blank('run_id')} AND NOT starts_with(file_name, run_id || '.')")
    _fail(con, report, F, F, "converter_version", "converter_version is required for mzml files",
          f"kind = 'mzml' AND {_blank('converter_version')}")
    _fail(con, report, "run_manifest", "run_manifest", "run_id", "run has no raw_vendor file in file_manifest",
          "run_status = 'ok' AND run_id NOT IN (SELECT run_id FROM file_manifest WHERE kind = 'raw_vendor' AND run_id IS NOT NULL)")
    # calibration points: the amount must be derivable
    C = "calibration_points"
    con.execute(
        "CREATE OR REPLACE TEMP VIEW cal_std AS SELECT c._row, c.run_id, c.aroma_id, "
        "CASE WHEN substr(r.sample_id,1,3) = 'STD' THEN r.sample_id ELSE s.parent_std_id END AS std_id, r.run_type "
        "FROM calibration_points c JOIN run_manifest r USING (run_id) "
        "LEFT JOIN sample_manifest s ON s.sample_id = r.sample_id AND s.aliquot = r.aliquot")
    n_bad = con.execute(
        "SELECT count(*) FROM cal_std WHERE run_type NOT IN ('std', 'spiked')").fetchone()[0]
    if n_bad:
        report.error("calibration_points", "run_id", f"{n_bad} rows belong to runs that are not standard or spiked runs")
    n_bad = con.execute(
        "SELECT count(*) FROM cal_std v WHERE run_type IN ('std', 'spiked') AND NOT EXISTS "
        "(SELECT 1 FROM standard_components k WHERE k.std_id = v.std_id AND k.aroma_id = v.aroma_id)").fetchone()[0]
    if n_bad:
        rows = con.execute(
            "SELECT run_id, aroma_id, std_id FROM cal_std v WHERE run_type IN ('std', 'spiked') AND NOT EXISTS "
            "(SELECT 1 FROM standard_components k WHERE k.std_id = v.std_id AND k.aroma_id = v.aroma_id) LIMIT 5").fetchall()
        report.error("calibration_points", "aroma_id",
                     f"{n_bad} rows name a compound that is not in the standard used, so no amount can be derived, for example {rows}")
    # a calibration point needs a lab-set range flag consistency
    _fail(con, report, C, C, "in_range", "use_for_lod is Y but in_range is N",
          "use_for_lod = 'Y' AND in_range = 'N'")


def check_submission(folder, lab=None, standards_dir=None):
    """Check one submission folder. Returns (Report, connection)."""
    folder = Path(folder)
    report = Report()
    con = duckdb.connect()
    load_compounds(con)
    for name in ("standards", "standard_components"):
        path = Path(standards_dir) / f"{name}.csv" if standards_dir else ROOT / TABLES[name]["path"]
        load_table(con, name, path, report, label=name)
    # Run, sample and file manifests are required only when the folder carries run level data.
    has_runs = any((folder / f"{n}.csv").exists() for n in ("calibration_points", "features"))
    for name, spec in TABLES.items():
        if spec["where"] != "lab":
            continue
        load_table(con, name, folder / f"{name}.csv", report, optional=spec["optional"] or not has_runs, label=name)
    for name, spec in TABLES.items():
        if spec["where"] == "lab":
            check_columns(con, name, report)
    for name, spec in TABLES.items():
        if spec["where"] == "lab":
            check_foreign_keys(con, name, report)
    if report.ok():
        cross_checks(con, report, lab)
    return report, con


def check_central(con, report):
    """Check the UoM-owned registry tables."""
    for name, spec in TABLES.items():
        if spec["where"] == "central" and name not in ("standards", "standard_components"):
            load_table(con, name, ROOT / spec["path"], report, label=name)
    for name, spec in TABLES.items():
        if spec["where"] == "central":
            check_columns(con, name, report)
            check_foreign_keys(con, name, report)
