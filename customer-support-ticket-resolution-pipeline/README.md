#  Support Ticket Resolution Analytics Pipeline (Azure + Databricks)

## Project Overview

This project implements an end-to-end Data Engineering pipeline using the Medallion Architecture (Raw → Bronze → Silver → Gold) on Azure Data Lake Storage Gen2 and Azure Databricks.

The pipeline processes customer support ticket data, applies business validation rules, and generates leadership-ready KPIs for measuring support team performance.

Since the company did not provide sample datasets, realistic raw CSV files were generated to simulate production data while preserving a real-world ETL workflow.

---

# Tech Stack

- Azure Data Lake Storage Gen2 (ADLS Gen2)
- Azure Databricks
- Apache Spark (PySpark)
- Delta Lake
- Python
- Azure for Students Subscription

---

# 📂 Project Structure

```
Support-Pipeline-Project/
│
├── notebooks/
│   ├── 01_generate_raw_data.ipynb
│   ├── 02_bronze_ingestion.ipynb
│   ├── 03_validation.ipynb
│   ├── 04_silver_transform.ipynb
│   └── 05_gold_aggregations.ipynb
│
├── sample_data/
│   ├── agent_profiles.csv
│   ├── day1_tickets.csv
│   └── day2_tickets.csv
│
├── screenshots/
│   ├── adls_folder_structure.png
│   ├── gold_tables_output.png
│   └── dashboard.png (optional)
│
└── README.md
```

---

#  Architecture

```
Raw CSV Files
        │
        ▼
Bronze Layer (Delta)
        │
        ▼
Validation
        │
        ▼
Silver Layer
        │
        ▼
Business Rules
        │
        ▼
Gold Layer
        │
        ▼
Business KPIs
```

---

# 📁 Raw Layer

The following datasets were generated to simulate operational data:

- agent_profiles.csv
- day1_tickets.csv
- day2_tickets.csv

The raw files contain intentionally messy data, including:

- Missing values
- Invalid records
- Out-of-scope Team Leads
- Mixed ticket statuses
- Resolution times stored as text

---

# 🥉 Bronze Layer

Purpose:

- Preserve raw source data
- Apply explicit schemas
- Add ingestion timestamp
- Store data in Delta format

No business transformations are applied in this layer.

---

# ✅ Validation Layer

Validation rules:

- Remove rows with missing Ticket ID
- Remove rows with missing Agent ID
- Remove rows with missing Resolution Time

Rejected records are stored separately for auditing.

---

# 🥈 Silver Layer

Transformations performed:

### Resolution Time Conversion

Converted values such as

```
1h 18m 42s
```

into

```
Decimal Minutes
```

Business rounding rule:

- Seconds ≥ 30 → Round Up
- Seconds < 30 → Round Down

---

### Join

Joined ticket data with Agent Profiles.

---

### Scope Filter

Included only Team Leads:

- TL01
- TL02
- TL03
- TL04
- TL05
- TL06
- TL07
- TL08

Removed:

- TL09
- TL12

---

### Business Rule

A ticket qualifies only when:

- Status = Resolved
- Resolution Time > 15 minutes

---

### Carry-over Rule

If an agent already qualified on Day 1,

their Day 2 records are excluded to avoid double-counting.

---

# 🥇 Gold Layer

Generated business-ready KPI tables.

### Q1

Team Lead Performance

Metrics:

- Total Resolved Tickets
- Number of Agents
- Average Tickets per Agent

---

### Q2

Agent Performance

Comparison:

- Day 1 Resolution Count
- Day 2 Resolution Count
- Performance Trend

Trend values:

- Improved
- Stable
- Declined

---

### Q3

Compliance Rate

Calculated:

```
Qualified Resolved Tickets
--------------------------
All Resolved Tickets
```

Displayed as percentage.

---

### Q4

Carry-over Agents

Lists agents whose Day 2 tickets were removed because they already qualified on Day 1.

---

#  Business KPIs

The pipeline generates:

- Team Lead Performance
- Agent Daily Performance
- Compliance Rate
- Carry-over Agents

---

# 📂 Storage Structure

```
raw/
    agent_profiles.csv
    day1_tickets.csv
    day2_tickets.csv

bronze/
    agent_profiles
    day1_tickets
    day2_tickets

silver/
    day1_valid
    day2_valid
    day1_scoped
    day2_scoped
    carryover_agents
    combined_qualified_tickets

gold/
    q1_team_lead_performance
    q2_agent_daily_performance
    q3_compliance_rate
    q4_carryover_agents
```

---

# ✅ Data Quality Checks

Verified:

- Bronze row counts match Raw files
- Invalid records removed during Validation
- Silver contains only business-qualified records
- Carry-over rule correctly removes duplicate Day 2 agents
- Gold KPIs match Silver aggregates

---

#  Screenshots

Included:

- ADLS Folder Structure
- Gold Layer Output
- Dashboard (Optional)

---

#  Future Improvements

- Automated workflow using Databricks Workflows
- Parameterized notebooks using Databricks Widgets
- Unity Catalog integration
- Incremental data loading with Auto Loader
- Power BI Dashboard integration

---

# Author

**Shanvi Shrivastava**

B.Tech Computer Science Engineering

Azure • Databricks • PySpark • Delta Lake • Data Engineering
