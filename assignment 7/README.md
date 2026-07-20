# Delta Lake MERGE Implementation — Incremental Data Processing (SCD Type 1 & Type 2)

## Objective
Perform incremental data processing using Delta Lake's `MERGE INTO` operation, implementing
both **SCD Type 1** (overwrite) and **SCD Type 2** (full history) patterns.

## Folder Structure
```
delta-lake-assignment/
│
├── data/
│   ├── customer_master.csv                # Target table (raw, with a few nulls/dupes to clean)
│   ├── customer_incremental.csv           # Source table (updates + brand-new customers)
│   ├── customer_master_scd1_final.csv     # Output: SCD1 merged result
│   ├── customer_master_scd2_final.csv     # Output: SCD2 merged result (with history)
│   └── delta_table_customer*/             # Parquet-backed "Delta table" versions
│
├── notebooks/
│   └── delta_scd_assignment.ipynb         # Full, executed implementation
│
├── screenshots/
│   ├── data_loading/
│   ├── data_cleaning/
│   ├── scd1/
│   ├── scd2/
│   ├── validation/
│   └── final_output/
│   (see screenshots/README.md — capture these after running the notebook locally)
│
├── report/
│   └── assignment_summary.md              # Short written explanation (optional PDF export)
│
└── README.md
```

## What the notebook does
1. **Load** `customer_master.csv` into a Delta-table-style Parquet store.
2. **Clean** the data — fills missing `city`/`segment` values, removes exact duplicate rows.
3. **Creates** `customer_incremental.csv` scenario — 20 existing customers with changed
   attributes + 10 brand-new customers.
4. **SCD Type 1 MERGE** — matched rows are overwritten in place, unmatched rows inserted.
   Exactly one row per `customer_id`, no history retained.
5. **SCD Type 2 MERGE** — matched rows whose tracked attributes changed are *expired*
   (`is_current = False`, `effective_end_date` set) and a new *current* version is
   inserted; brand-new customers are inserted as current. Full history is preserved.
6. **Validates** results: row-count reconciliation, no duplicate `customer_id` values in
   SCD1, exactly one current row per customer in SCD2, no expired row missing an end date.
7. **Displays** the final datasets and prints a run summary.


## How to run
```bash
cd notebooks
jupyter notebook delta_scd_assignment.ipynb
```
Run all cells top to bottom. Take the screenshots listed in `screenshots/README.md` as you go.

## GitHub Submission Checklist
- [ ] Upload this whole `delta-lake-assignment/` folder to a GitHub repo
- [ ] Confirm the notebook runs top-to-bottom without errors
- [ ] Add screenshots to each subfolder under `screenshots/`
- [ ] (Optional) Export `report/assignment_summary.md` to PDF for `report/assignment_summary.pdf`
- [ ] Push and share the repo link
