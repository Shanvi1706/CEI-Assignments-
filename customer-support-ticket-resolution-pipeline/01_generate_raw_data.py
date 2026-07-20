# Databricks notebook source
dbutils.widgets.text("storage_account", "stsupportpipelineshanvi")

storage_account = dbutils.widgets.get("storage_account")

RAW = f"abfss://raw@{storage_account}.dfs.core.windows.net/"
BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"
SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"
GOLD = f"abfss://gold@{storage_account}.dfs.core.windows.net/"

# COMMAND ----------

storage_account = "stsupportpipelineshanvi"

RAW = f"abfss://raw@{storage_account}.dfs.core.windows.net/"

# COMMAND ----------

import random
import pandas as pd

random.seed(42)

team_leads_in_scope = [f"TL{i:02d}" for i in range(1, 9)]      # TL01–TL08
team_leads_out_of_scope = ["TL09", "TL12"]

agents = []
agent_num = 1
# 5 agents per in-scope team lead = 40 agents
for tl in team_leads_in_scope:
    for _ in range(5):
        agents.append({
            "agent_id": f"A{agent_num:03d}",
            "agent_name": f"Agent_{agent_num:03d}",
            "role": "Support Agent",
            "team_lead_id": tl
        })
        agent_num += 1

# 2 agents outside scope
for tl in team_leads_out_of_scope:
    agents.append({
        "agent_id": f"A{agent_num:03d}",
        "agent_name": f"Agent_{agent_num:03d}",
        "role": "Support Agent",
        "team_lead_id": tl
    })
    agent_num += 1

agent_profiles_df = pd.DataFrame(agents)
agent_profiles_spark = spark.createDataFrame(agent_profiles_df)

(agent_profiles_spark
    .coalesce(1)
    .write
    .mode("overwrite")
    .option("header", True)
    .csv(RAW + "agent_profiles"))

display(agent_profiles_spark)

# COMMAND ----------

import random

def random_time_string():
    h = 0
    m = random.randint(0, 90)
    s = random.randint(0, 59)
    return f"{h}h {m}m {s}s"

def generate_tickets(day, agent_ids, n_valid, n_null, n_out_of_scope, out_of_scope_ids, ticket_start):
    rows = []
    tid = ticket_start

    # valid rows (mix of Resolved / Pending / In Progress)
    for _ in range(n_valid):
        rows.append({
            "ticket_id": f"T{tid:05d}",
            "agent_id": random.choice(agent_ids),
            "status": random.choices(["Resolved", "Pending", "In Progress"], weights=[70, 20, 10])[0],
            "resolution_time": random_time_string()
        })
        tid += 1

    # null / bad rows — missing fields
    for _ in range(n_null):
        rows.append({
            "ticket_id": f"T{tid:05d}" if random.random() > 0.3 else None,
            "agent_id": random.choice(agent_ids) if random.random() > 0.3 else None,
            "status": "Resolved",
            "resolution_time": None
        })
        tid += 1

    # out-of-scope agent rows
    for _ in range(n_out_of_scope):
        rows.append({
            "ticket_id": f"T{tid:05d}",
            "agent_id": random.choice(out_of_scope_ids),
            "status": "Resolved",
            "resolution_time": random_time_string()
        })
        tid += 1

    return pd.DataFrame(rows)

in_scope_ids = agent_profiles_df[agent_profiles_df.team_lead_id.isin(team_leads_in_scope)].agent_id.tolist()
out_scope_ids = agent_profiles_df[agent_profiles_df.team_lead_id.isin(team_leads_out_of_scope)].agent_id.tolist()

day1_df = generate_tickets("Day1", in_scope_ids, n_valid=119, n_null=4, n_out_of_scope=6,
                            out_of_scope_ids=out_scope_ids, ticket_start=1)
day2_df = generate_tickets("Day2", in_scope_ids, n_valid=84, n_null=2, n_out_of_scope=4,
                            out_of_scope_ids=out_scope_ids, ticket_start=1000)

# Convert Pandas DataFrames to Spark DataFrames
day1_spark = spark.createDataFrame(day1_df)
day2_spark = spark.createDataFrame(day2_df)

# Write Day 1 tickets to the Raw layer
(day1_spark
    .coalesce(1)
    .write
    .mode("overwrite")
    .option("header", True)
    .csv(RAW + "day1_tickets"))

# Write Day 2 tickets to the Raw layer
(day2_spark
    .coalesce(1)
    .write
    .mode("overwrite")
    .option("header", True)
    .csv(RAW + "day2_tickets"))

# Display the generated data
display(day1_spark)
display(day2_spark)

# COMMAND ----------

display(dbutils.fs.ls(RAW))