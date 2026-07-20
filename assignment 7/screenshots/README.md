# Screenshots Guide

Screenshots must be captured by you while running `notebooks/delta_scd_assignment.ipynb`
locally or in Databricks (they can't be generated in this sandboxed environment). Place
them in the matching subfolder below.

| Folder | What to capture |
|---|---|
| `data_loading/` | Output of the "Load the Dataset into a Delta Table" cell — the `master_raw.head()` table and row/column count print. |
| `data_cleaning/` | The missing-values summary print, the "Missing values after fill: 0" line, and the duplicate-removal print showing the shape change. |
| `scd1/` | The SCD1 merge cell output (row counts) and the "Before merge / After SCD1 merge" comparison for the example customer. |
| `scd2/` | The SCD2 merge cell output (rows expired / new versions inserted) and the "Full history" table for the example customer showing both the expired and current rows. |
| `validation/` | Both validation cells' full printed output, including the "All validation checks passed." line. |
| `final_output/` | The two "Final table" display cells (SCD1 sample and SCD2 current-rows sample) and the final "Saved:" confirmation print. |
