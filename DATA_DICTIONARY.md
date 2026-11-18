# AROMA submission data dictionary

Generated from schema/submission_tables.json. Do not edit by hand.

Every table is a UTF-8 CSV with a header row, comma separated, one record per line, blank for missing. Dates are YYYY-MM-DD. Date and time values are ISO 8601 with a UTC offset, for example 2027-02-09T10:15:00+00:00. Booleans are Y or N. Decimal point, never a comma.

## standards

One row per standard preparation. Issued and owned by UoM.

Held by: UoM, in the central registry. Table is required in a submission. Unique key: std_id.

- std_id: required, string, pattern ^STD[0-9]{7}$. Standard identifier issued by UoM.
- prepared_date: required, date. Date of gravimetric preparation.
- prep_batch: required, string. UoM preparation batch.
- carrier: required, string. Solvent or carrier the standard is held in.
- level_label: optional, string. Free label for the concentration level.

## standard_components

Which compounds are in each standard and at what concentration. One row per standard and compound, so mixtures of any size are held in the same table.

Held by: UoM, in the central registry. Table is required in a submission. Unique key: std_id, aroma_id.

- std_id: required, string.
- aroma_id: required, string, pattern ^AROMA-[0-9]{6,8}$.
- conc_ng_per_ml: required, number, greater than 0. Certified concentration of the compound in the standard, ng per mL.
- expanded_uncertainty_percent: optional, number, minimum 0.
- coverage_factor: optional, number, greater than 0.
- purity_percent: required, number, minimum 0, maximum 100.
- supplier: required, string.

## sample_manifest

One row per aliquot analysed by the laboratory. The mandatory collection fields are required for every sample type except standards.

Held by: the submitting laboratory. Table is required in a submission. Unique key: sample_id, aliquot.

- sample_id: required, string, pattern ^(STD|SPK|BLK|QCP|SMP)[0-9]{7}$. Prefix gives the sample type. STD is issued by UoM. SPK, BLK, QCP and SMP are issued by the laboratory from its own block in registry/id_blocks.csv.
- aliquot: required, string, pattern ^A[0-9]{1,2}$. Aliquot of the sample, for example A1. Unique across the consortium for a given sample.
- sample_type: required, string, one of the codes in registry/vocab/sample_types.csv. Must match the sample_id prefix.
- matrix_code: required, string, one of the codes in registry/vocab/matrices.csv. neat for standards.
- parent_std_id: required for SPK, string, pattern ^STD[0-9]{7}$. Standard used to spike the matrix.
- holding_lab: required, string, one of the codes in registry/vocab/labs.csv. Laboratory that analyses this aliquot.
- collection_datetime: required except for standards, datetime.
- collection_device: required except for standards, string.
- sorbent: required except for standards, string.
- volume_ml: required except for standards, number, minimum 0.
- flow_ml_min: required except for standards, number, minimum 0.
- temperature_c: required except for standards, number.
- rel_humidity_pct: required except for standards, number, minimum 0, maximum 100.
- storage_duration_h: required except for standards, number, minimum 0.
- transport_conditions: required except for standards, string.

## sample_attributes

Stream-specific fields in long format, so a new matrix needs a new vocabulary entry and not a new column.

Held by: the submitting laboratory. Table is optional in a submission. Unique key: sample_id, aliquot, attribute.

- sample_id: required, string.
- aliquot: required, string.
- attribute: required, string, one of the codes in registry/vocab/stream_attributes.csv.
- value: required, string.

## run_manifest

One row per acquisition. The run_id is the file name without its extension and encodes lab, platform, date, sample, aliquot and run number.

Held by: the submitting laboratory. Table is required in a submission. Unique key: run_id.

- run_id: required, string, pattern ^[A-Z][A-Z0-9]{1,5}_[A-Z0-9]{3,8}_[0-9]{8}_(STD|SPK|BLK|QCP|SMP)[0-9]{7}-A[0-9]{1,2}_R[0-9]{2}_[0-9]{4}$. LAB_PLATFORM_YYYYMMDD_SAMPLEID-ALIQUOT_Rnn_RUNNO, the file name without its extension.
- lab: required, string, one of the codes in registry/vocab/labs.csv.
- platform: required, string, one of the codes in registry/vocab/platforms.csv.
- run_date: required, date.
- sample_id: required, string.
- aliquot: required, string, pattern ^A[0-9]{1,2}$.
- run_no: required, int, minimum 1, maximum 9999.
- replicate: required, int, minimum 1, maximum 99.
- batch_id: required, string, pattern ^[0-9]{8}_B[0-9]{2}$.
- run_type: required, string, one of the codes in registry/vocab/run_types.csv.
- run_status: required, string, one of the codes in registry/vocab/run_status.csv.
- status_note: optional, string.
- injection_datetime: required, datetime.
- instrument_id: required, string.
- method_id: required, string.
- sop_id: required, string.
- sop_version: required, string.
- delivered_volume_ul: optional, number, minimum 0. Volume of standard loaded, injected or spiked. Required for std and spiked runs.
- processing_software: required, string. Software used to extract the compound responses, for example MassHunter, MS-DIAL, TargetLynx.
- processing_version: required, string. Version of that software, and the processing method file name if there is one.
- internal_standard: optional, string.

## file_manifest

One row per file, raw or exported. Raw vendor folders are archived as a single zip so that one checksum covers them.

Held by: the submitting laboratory. Table is required in a submission. Unique key: file_name.

- file_name: required, string.
- run_id: optional, string. Required for raw_vendor and mzml files.
- kind: required, string, one of the codes in registry/vocab/file_kinds.csv (kind column).
- sha256: required, string, pattern ^[a-f0-9]{64}$.
- size_bytes: required, int, minimum 0.
- uri: optional, string.
- converter_version: optional, string. For example the msconvert version used to make an mzML file.

## calibration_points

One response per run and compound. The amount is never typed by the laboratory. It is derived from the standard registry and the delivered volume in the run manifest.

Held by: the submitting laboratory. Table is optional in a submission. Unique key: run_id, aroma_id.

- run_id: required, string.
- aroma_id: required, string.
- response: required, number.
- response_basis: required, string, one of the codes in registry/vocab/response_basis.csv.
- quant_ion: required, string. Ion or transition quantified, for example 117.0578 or 118.065>91.054.
- use_for_lod: required, bool. Point lies in the low range set by the SOP for LOD and LOQ.
- in_range: required, bool. Point lies in the laboratory's reported linear range.

## features

Harmonised feature table, one row per run and feature. Unassigned features are kept, with a blank aroma_id.

Held by: the submitting laboratory. Table is optional in a submission. Unique key: run_id, feature_id.

- run_id: required, string.
- feature_id: required, string.
- aroma_id: optional, string.
- rt_min: optional, number, minimum 0.
- mz: required, number, greater than 0.
- adduct: optional, string, one of the codes in registry/vocab/adducts.csv.
- area: optional, number.
- area_is_ratio: optional, number.
- id_level: optional, string, one of the codes in registry/vocab/id_levels.csv.
- snr: optional, number.
- flags: optional, string. Semicolon separated QC flags.

## ccs_results

One row per laboratory, platform, compound, adduct, buffer gas and method. The expanded uncertainty states its coverage factor.

Held by: the submitting laboratory. Table is optional in a submission. Unique key: lab, platform, aroma_id, adduct, buffer_gas, method.

- lab: required, string, one of the codes in registry/vocab/labs.csv.
- platform: required, string, one of the codes in registry/vocab/platforms.csv.
- aroma_id: required, string.
- adduct: required, string, one of the codes in registry/vocab/adducts.csv.
- buffer_gas: required, string, one of the codes in registry/vocab/buffer_gases.csv.
- method: required, string, one of the codes in registry/vocab/ccs_methods.csv.
- calibrant: required, string.
- ccs_a2: required, number, greater than 0.
- expanded_uncertainty_a2: required, number, minimum 0.
- coverage_factor: required, number, greater than 0.
- n_replicates: required, int, minimum 1.
- confidence: required, string. Confidence statement. A controlled vocabulary is still to be agreed.

## perception_summary

Open-tier aggregates only, released by UoM after disclosure review. Session-level and assessor-level data stay in the controlled tier.

Held by: UoM, in the central registry. Table is required in a submission. Unique key: aroma_id.

- aroma_id: required, string.
- detection_level: optional, number.
- quality_change_level: optional, number.
- gco_neat: optional, number.
- gco_in_matrix: optional, number.
- level_unit: required, string.
- intensity: optional, number.
- intensity_scale: optional, string.
- descriptor: optional, string.
- assessors_n: required, int, minimum 1.
- lexicon_version: required, string.
- disclosure_reviewed: required, bool. Must be Y before a row can enter the open tier.

## release_status

Set by reviewers once a card passes QC or is released.

Held by: UoM, in the central registry. Table is required in a submission. Unique key: aroma_id.

- aroma_id: required, string.
- status: required, string, one of the codes in registry/vocab/release_status.csv.
- release_id: required, string.
