# E-Commerce Order Analytics System

An end-to-end analytics pipeline that generates messy e-commerce data,
cleans and validates it, loads it into SQLite, runs business-intelligence
SQL (joins, window functions, CTEs, cohort analysis), and exposes the
results through a command-line reporting tool.

## 1. Architecture

```
Raw data (Faker)  --generate_data.py-->  data/raw/*.csv
                                              |
                                    clean_data.py (Pandas)
                                              v
                                   data/cleaned/*.csv + data quality report
                                              |
                                       load_db.py (schema.sql)
                                              v
                                        ecommerce.db (SQLite)
                                              |
                        sql/*.sql  <---  report_cli.py (argparse + sqlite3)
                                              v
                                   output/sample_reports/*.txt
```

**Design choices**

- **Referential integrity**: `orders.order_id` is the single source of
  truth. `order_items` rows that reference a non-existent `order_id`
  are detected by `check_referential_integrity()` and removed during
  cleaning (`orphan_items_removed` in the data quality report),
  rather than causing FK errors at load time.
- **Missing `customer_id`**: rather than dropping the order (which would
  under-count revenue), it is standardized to the literal string
  `'UNKNOWN'` so it's easy to filter out of customer-level reports
  (`WHERE customer_id <> 'UNKNOWN'`) while still counting toward
  order/revenue totals.
- **Negative quantity**: treated as returns, not deleted. An `is_return`
  flag column is added in `order_items` so return-rate analysis (Q5, Q6)
  can be computed without losing information.
- **Bad date formats**: `DD-MM-YYYY` rows are detected and converted to
  the canonical `YYYY-MM-DD HH:MM:SS`. Rows with genuinely unparseable
  dates are dropped and counted separately in the report.

## 2. Folder Structure

```
ecommerce-analytics-system/
├── data/
│   ├── raw/                 # generated raw CSVs (intentionally messy)
│   └── cleaned/              # cleaned CSVs, ready to load
├── scripts/
│   ├── generate_data.py      # Part 1: synthetic data generation
│   ├── clean_data.py         # Part 2: cleaning + validation functions
│   ├── load_db.py            # loads cleaned CSVs into SQLite
│   ├── report_cli.py         # Part 4 / Step 8: CLI reporting tool
│   └── test_edge_cases.py    # Part 5 / Step 9: edge case tests
├── sql/
│   ├── schema.sql             # table DDL with PK/FK/CHECK constraints
│   ├── aggregations.sql       # Q1-Q6: joins & aggregations
│   ├── window_functions.sql   # Q7-Q9, Q11, Q13, Q14, Q16
│   └── cohort_analysis.sql    # Q10, Q12, Q15: multi-level CTEs, YoY, cohorts
├── output/
│   └── sample_reports/        # data_quality_report.txt + sample CLI output
├── ecommerce.db                # generated SQLite database (after load_db.py)
└── README.md
```

## 3. How to Run

```bash
cd scripts

# 1. Generate raw (messy) data -> ../data/raw/*.csv
python3 generate_data.py

# 2. Clean + validate -> ../data/cleaned/*.csv + data quality report
python3 clean_data.py

# 3. Load cleaned data into SQLite -> ../ecommerce.db
python3 load_db.py

# 4. Explore the SQL queries directly (any SQLite client), e.g.:
#    sqlite3 ../ecommerce.db < ../sql/aggregations.sql

# 5. Run the CLI reporting tool
python3 report_cli.py --report summary --type monthly --start 2024-01-01 --end 2024-01-31
python3 report_cli.py --report top_customers
python3 report_cli.py --report retention

# Interactive mode (prompts for report type & dates):
python3 report_cli.py

# 6. Run the edge case tests
python3 test_edge_cases.py
```

## 4. CLI Reporting Tool

`report_cli.py` supports three report types:

| Report          | Flags                                              | Description                                   |
|-----------------|-----------------------------------------------------|------------------------------------------------|
| `summary`       | `--type daily/weekly/monthly --start YYYY-MM-DD --end YYYY-MM-DD` | Orders, revenue, unique customers, top 3 products, and % change vs. the immediately preceding period of equal length. |
| `top_customers` | *(none)*                                             | Top 10 customers by total order value.         |
| `retention`     | *(none)*                                             | Cohort-based retention (month 0-3) by registration month. |

It validates dates, checks the DB connection before querying, and
handles empty result sets gracefully (prints `(no data)` instead of
crashing) — see Part 5 requirements.

## 5. SQL Query Index

| # | Query | File |
|---|-------|------|
| 1 | Total revenue per category | `aggregations.sql` |
| 2 | Top 10 customers by order value | `aggregations.sql` |
| 3 | Month-wise order count (last 12 months) | `aggregations.sql` |
| 4 | Customers with no delivered items | `aggregations.sql` |
| 5 | Products with more returns than purchases | `aggregations.sql` |
| 6 | Return rate per category | `aggregations.sql` |
| 7 | Running total of revenue per region | `window_functions.sql` |
| 8 | DENSE_RANK products by revenue per category | `window_functions.sql` |
| 9 | LAG: days between consecutive orders + "At Risk" flag | `window_functions.sql` |
| 10 | Multi-level CTE: monthly revenue → spend tier → counts | `cohort_analysis.sql` |
| 11 | NTILE customer quartiles (Platinum/Gold/Silver/Bronze) | `window_functions.sql` |
| 12 | Year-over-year revenue comparison | `cohort_analysis.sql` |
| 13 | First/last purchased category (category shift) | `window_functions.sql` |
| 14 | Cumulative revenue distribution | `window_functions.sql` |
| 15 | Cohort retention analysis (month 0-3) | `cohort_analysis.sql` |
| 16 | Self-join: products frequently bought together | `window_functions.sql` |

## 6. Edge Cases Covered (Part 5 / Step 9)

`scripts/test_edge_cases.py` verifies:

1. `order_items` rows referencing a non-existent `order_id` are detected
   and removed (orphan rows), row counts logged.
2. `discount_percent > 100` is clipped to 100 and counted as an anomaly.
3. `quantity == 0` rows are flagged (not silently dropped) — they
   contribute 0 revenue and are neither a purchase nor a return.
4. `order_date` in the future is preserved (a business-logic anomaly,
   not a formatting error) so it can be surfaced by downstream
   reporting rather than silently "corrected".

The CLI tool separately handles: missing database file, invalid date
input, `start > end`, and empty result sets.

## 7. Sample Output

See `output/sample_reports/`:
- `data_quality_report.txt` — issues found during cleaning
- `summary_monthly_sample.txt` — sample monthly summary report
- `top_customers_sample.txt` — sample top-customers report
- `retention_sample.txt` — sample cohort retention report

## 8. Requirements

- Python 3.9+
- `pandas`, `Faker` (data generation & cleaning only)
- `sqlite3` (standard library — used by `load_db.py` and `report_cli.py`)

```bash
pip install pandas faker --break-system-packages
```
