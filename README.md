# AROMA submission guidance

Public guidance for laboratories contributing data to the Molecular Olfaction Commons (AROMA). Everything a laboratory needs to prepare a submission is on this page, so nothing has to be opened or downloaded to follow the steps. The only file to download is the workbook, Submission template v1.xlsx, which every laboratory fills in.

Version 0.2, a proposal for the five laboratories in the sprint (UoM, EES, LU, UoR and WYT). The rules hold when the consortium grows to 25 laboratories and 50,000 compounds or more, so nothing here depends on the number of laboratories or compounds.

## 1. What you send

For every batch, send three things.

1. The filled workbook, Submission template v1.xlsx, in this repository. It is the only template. Every laboratory fills in the same sheets.
2. The raw files, named as in section 3, with a SHA-256 checksum for each listed in the workbook.
3. The same data converted to the open format in section 4.

The raw files are deposited in institutional storage and never go on GitHub. The workbook holds the metadata, the compound responses and the file list.

## 2. Identifiers

- Compounds: AROMA-NNNNNN, 6 to 8 digits. Issued by the registry, never by a laboratory.
- Standards: STD followed by 7 digits. UoM issues all of them, because UoM prepares all standards.
- Spiked samples, blanks, pooled QC and real samples: SPK, BLK, QCP and SMP followed by 7 digits. Each laboratory issues its own from its own block in registry/id_blocks.csv. Laboratories make their own matrices, their own blanks and their own spikes, using only the standards UoM supplies. Each spiked sample records the STD it was spiked from.
- Aliquot: A followed by 1 or 2 digits, for example A1. An aliquot belongs to one laboratory, so the same tube split between two laboratories has two aliquot numbers.
- Laboratory and platform codes are in the Vocabularies sheet. Codes use capital letters and digits and never an underscore.

## 3. Raw data file names

    LAB_PLATFORM_YYYYMMDD_SAMPLEID-ALIQUOT_Rnn_RUNNO.ext

Example: LU_TDGCMS_20270209_SMP0000123-A1_R01_0042.raw

- The sample type is the ID prefix, so it is not repeated. Matrix and all other metadata live in the workbook, so a name cannot contradict it.
- Rnn is the replicate. RUNNO has 4 digits and is unique within the laboratory and day.
- Vendor folders (.d and .raw directories) are zipped into one file with the same stem, so that one checksum covers the run.
- Names contain no spaces, because pipelines break on spaces.
- A corrected file is a new version with a new run number. Never overwrite or rename a submitted file.
- Keep batches in a folder named YYYYMMDD_Bnn.

The authority is the run_manifest sheet, and the checker confirms that the file names and the sheet agree.

## 4. Formats

- Raw: the vendor-native file, unaltered, zipped per run.
- Open copy: mzML, converted with ProteoWizard msconvert. Record the converter and its version in the file_manifest sheet. Whether the ion mobility dimension survives conversion differs by vendor, so each laboratory should test one file and report the result before the first batch.
- Tables: the workbook, or UTF-8 CSV with the same headers for tables over about 50,000 rows. Decimal point, not comma.
- Dates are YYYY-MM-DD. Date and time values are ISO 8601 with a UTC offset, typed as text.
- Human-linked metadata and session-level perception data never go in the workbook. They stay in the controlled tier.

## 5. Do laboratories deconvolve and send compound data?

The database holds one response per run and compound, so someone has to turn raw data into compound responses. For the sprint, each laboratory does this with its own software and sends the result. This keeps the sprint moving, and it is the most practical route for standards, where the compound, retention window and quantifier ion are known, so targeted integration is enough.

To keep the results comparable, the workbook records how each response was made.

- processing_software and processing_version on every run.
- quant_ion on every response, the ion or transition that was integrated.
- use_for_lod and in_range flags, set from the SOP.
- The features sheet for untargeted features, with unassigned features kept.

Because the raw and mzML files are deposited with checksums, the consortium can later reprocess every run with one common pipeline and compare it with the laboratory results. That central reprocessing is a later layer and is not needed for the sprint.

## 6. Check before sending

    python scripts/check_submission.py "your file.xlsx" -lab YOURCODE

The checker is distributed to partner laboratories by the consortium. It tests every column, the links between sheets, the agreement between file names and the run_manifest, whether an amount can be derived for every compound response, and whether each sample ID is inside an allocated block. Fix every error before sending. Nothing is changed by the checker.

## 7. What happens next

The AROMA build loads all submissions into one database, derives LOD, LOQ, linear range, matrix effect, CCS summary and provenance counts under DEFINITIONS.md, and regenerates every card. Keep blanks, failed runs and runs excluded after QC, marked with run_status and a note. They are retained and counted on the card.

## 8. The workbook sheets

One sheet per table. Required columns are marked with an asterisk. Sheets marked optional are filled in only when you have that kind of data. Allowed codes are listed in section 9 and in the workbook's Vocabularies sheet.

### sample_manifest

One row per aliquot analysed by the laboratory. The mandatory collection fields are required for every sample type except standards.

Columns: sample_id*, aliquot*, sample_type*, matrix_code*, parent_std_id, holding_lab*, collection_datetime*, collection_device*, sorbent*, volume_ml*, flow_ml_min*, temperature_c*, rel_humidity_pct*, storage_duration_h*, transport_conditions*

### sample_attributes (optional)

Stream-specific fields in long format, so a new matrix needs a new vocabulary entry and not a new column.

Columns: sample_id*, aliquot*, attribute*, value*

### run_manifest

One row per acquisition. The run_id is the file name without its extension and encodes lab, platform, date, sample, aliquot and run number.

Columns: run_id*, lab*, platform*, run_date*, sample_id*, aliquot*, run_no*, replicate*, batch_id*, run_type*, run_status*, status_note, injection_datetime*, instrument_id*, method_id*, sop_id*, sop_version*, delivered_volume_ul, processing_software*, processing_version*, internal_standard

### file_manifest

One row per file, raw or exported. Raw vendor folders are archived as a single zip so that one checksum covers them.

Columns: file_name*, run_id, kind*, sha256*, size_bytes*, uri, converter_version

### calibration_points (optional)

One response per run and compound. The amount is never typed by the laboratory. It is derived from the standard registry and the delivered volume in the run manifest.

Columns: run_id*, aroma_id*, response*, response_basis*, quant_ion*, use_for_lod*, in_range*

### features (optional)

Harmonised feature table, one row per run and feature. Unassigned features are kept, with a blank aroma_id.

Columns: run_id*, feature_id*, aroma_id, rt_min, mz*, adduct, area, area_is_ratio, id_level, snr, flags

### ccs_results (optional)

One row per laboratory, platform, compound, adduct, buffer gas and method. The expanded uncertainty states its coverage factor.

Columns: lab*, platform*, aroma_id*, adduct*, buffer_gas*, method*, calibrant*, ccs_a2*, expanded_uncertainty_a2*, coverage_factor*, n_replicates*, confidence*

## 9. Allowed codes

### Laboratories

| code | name |
|---|---|
| UOM | University of Manchester, Chemistry |
| EES | University of Manchester, Earth and Environmental Sciences |
| LU | Loughborough University |
| UOR | University of Reading |
| WYT | University of Manchester breath laboratory at Wythenshawe Hospital |

### Platforms

| code | name |
|---|---|
| GCQTOF | Gas chromatography quadrupole time-of-flight mass spectrometry |
| TDQQQ | Thermal desorption GC triple quadrupole mass spectrometry |
| TDGCMS | Thermal desorption gas chromatography mass spectrometry |
| GCMS | Gas chromatography mass spectrometry |
| TDGCO | Thermal desorption GC with olfactometry port |
| IMMS | Ion mobility mass spectrometry |
| DESI | Desorption electrospray ionisation mass spectrometry |
| CITOF | Chemical ionisation time-of-flight mass spectrometry |
| PTRMS | Proton transfer reaction mass spectrometry |

### Matrices

| code | display |
|---|---|
| neat | neat |
| sebum | sebum |
| breath | breath |
| food | food |
| fridge_air | fridge air |
| outdoor_air | outdoor air |
| test_house_air | test house air |

### Run types

| code |
|---|
| std |
| blank |
| qc |
| sample |
| spiked |

### Run status

| code |
|---|
| ok |
| failed |
| excluded |

### File kinds

| kind | extension |
|---|---|
| raw_vendor | raw |
| raw_vendor | d.zip |
| raw_vendor | raw.zip |
| raw_vendor | wiff |
| raw_vendor | wiff.zip |
| raw_vendor | qgd |
| raw_vendor | lcd |
| mzml | mzML |
| mzml | mzML.gz |
| feature_table | csv |
| feature_table | parquet |
| log | txt |
| other | zip |

### Identifier blocks

Each laboratory issues its own SPK, BLK, QCP and SMP numbers from its own block. UoM issues all STD numbers.

| Sample type | Issuer | First | Last |
|---|---|---|---|
| STD | UOM | 1 | 9999999 |
| SPK | UOM | 1 | 100000 |
| SPK | EES | 100001 | 200000 |
| SPK | LU | 200001 | 300000 |
| SPK | UOR | 300001 | 400000 |
| SPK | WYT | 400001 | 500000 |
| BLK | UOM | 1 | 100000 |
| BLK | EES | 100001 | 200000 |
| BLK | LU | 200001 | 300000 |
| BLK | UOR | 300001 | 400000 |
| BLK | WYT | 400001 | 500000 |
| QCP | UOM | 1 | 100000 |
| QCP | EES | 100001 | 200000 |
| QCP | LU | 200001 | 300000 |
| QCP | UOR | 300001 | 400000 |
| QCP | WYT | 400001 | 500000 |
| SMP | UOM | 1 | 100000 |
| SMP | EES | 100001 | 200000 |
| SMP | LU | 200001 | 300000 |
| SMP | UOR | 300001 | 400000 |
| SMP | WYT | 400001 | 500000 |

## 10. Where else to look

DATA_DICTIONARY.md lists every column with its type and rules in full. The same rules are built into the workbook, which has drop-down lists and a worked example on its Read me sheet.
