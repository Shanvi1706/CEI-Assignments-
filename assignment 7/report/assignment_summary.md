# Assignment Summary — Delta Lake MERGE Implementation

## What was built
A `customer_master` (target) and `customer_incremental` (source) dataset were derived
from the Superstore customer dimension. The notebook `delta_scd_assignment.ipynb`
loads, cleans, and merges these using Delta Lake's `MERGE INTO` semantics, implemented
in two flavors:

- **SCD Type 1** — the classic overwrite pattern (`WHEN MATCHED THEN UPDATE SET *`,
  `WHEN NOT MATCHED THEN INSERT *`). No history is kept; each customer has exactly one row.
- **SCD Type 2** — a history-preserving pattern using a two-phase MERGE: first expire
  the current row for any customer whose tracked attributes (`segment`, `city`) changed,
  then insert a new current version. Brand-new customers are inserted as current with
  no prior history.

## Results
| Metric | Value |
|---|---|
| Target rows (`customer_master`, after cleaning) | 793 |
| Nulls found & filled (`segment`, `city`) | 15 |
| Duplicate rows removed | 5 |
| Incremental rows (source) | 30 |
| Existing customers updated | 20 |
| Brand-new customers inserted | 10 |
| SCD1 result row count | 803 (793 target + 10 new) |
| SCD2 result row count | 823 (803 current + 20 historical) |

## Validation performed
- Row-count reconciliation: target + brand-new = SCD1 result count ✅
- No duplicate `customer_id` in the SCD1 result ✅
- Exactly one `is_current = True` row per `customer_id` in the SCD2 result ✅
- Every expired (historical) row has an `effective_end_date` populated ✅
- No customer from either the target or the incremental feed is missing a current row ✅

## Key takeaway
`MERGE INTO` is the core primitive for incremental/upsert processing in Delta Lake.
SCD Type 1 is a single MATCHED/NOT-MATCHED merge; SCD Type 2 requires staging the
"new version" rows and running the expire-then-insert pattern (or, in modern Databricks
pipelines, using the native `AUTO CDC ... INTO` API) so that closing old history and
opening new versions for the same key doesn't collide within a single MERGE statement.

## Environment limitation
No outbound access to Maven Central meant the Delta Lake JAR could not be fetched for a
live Spark session in this sandbox. The MERGE logic was implemented directly against a
Parquet-backed table with matching MATCHED/NOT-MATCHED semantics; equivalent real Delta
Lake SQL/PySpark snippets are included in the notebook for use in a connected environment.
