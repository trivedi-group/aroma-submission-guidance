# Guidance for laboratories submitting data to AROMA

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
