# Databricks notebook source
dbutils.widgets.text("storage_account", "stsupportpipelineshanvi")

storage_account = dbutils.widgets.get("storage_account")

RAW = f"abfss://raw@{storage_account}.dfs.core.windows.net/"
BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"
SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"
GOLD = f"abfss://gold@{storage_account}.dfs.core.windows.net/"

# COMMAND ----------

from pyspark.sql.functions import *
from pyspark.sql.types import *

silver = spark.read.format("delta").load(SILVER + "combined_qualified_tickets")

carryover = spark.read.format("delta").load(SILVER + "carryover_agents")

profiles = spark.read.format("delta").load(BRONZE + "agent_profiles")

day1_scoped = spark.read.format("delta").load(SILVER + "day1_scoped")

day2_scoped = spark.read.format("delta").load(SILVER + "day2_scoped")

# COMMAND ----------

storage_account = "stsupportpipelineshanvi"

SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"
GOLD = f"abfss://gold@{storage_account}.dfs.core.windows.net/"

# COMMAND ----------

from pyspark.sql.functions import *

# COMMAND ----------

silver = spark.read.format("delta").load(SILVER + "combined_qualified_tickets")

carryover = spark.read.format("delta").load(SILVER + "carryover_agents")

# COMMAND ----------

print("Qualified Tickets:", silver.count())
print("Carryover Agents:", carryover.count())

display(silver)

# COMMAND ----------

storage_account = "stsupportpipelineshanvi"

SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"
GOLD = f"abfss://gold@{storage_account}.dfs.core.windows.net/"
BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"

# COMMAND ----------

from pyspark.sql.functions import count, countDistinct, round as spark_round

q1_team_lead = (silver.groupBy("team_lead_id")
    .agg(
        count("ticket_id").alias("total_resolved"),
        countDistinct("agent_id").alias("num_agents")
    )
    .withColumn("avg_resolved_per_agent",
                spark_round(col("total_resolved")/col("num_agents"),2))
    .orderBy("team_lead_id"))

q1_team_lead.write.format("delta").mode("overwrite").save(GOLD+"q1_team_lead_performance")

display(q1_team_lead)

# COMMAND ----------

q2_agent_day = (silver.groupBy("agent_id","day")
    .agg(count("ticket_id").alias("resolved_count"))
    .groupBy("agent_id")
    .pivot("day",[1,2])
    .sum("resolved_count")
    .fillna(0)
    .withColumnRenamed("1","day1_resolved")
    .withColumnRenamed("2","day2_resolved"))

q2_agent_day = q2_agent_day.withColumn(
    "trend",
    when(col("day1_resolved")>col("day2_resolved"),"Declined")
    .when(col("day1_resolved")<col("day2_resolved"),"Improved")
    .otherwise("Stable")
)

q2_agent_day.write.format("delta").mode("overwrite").save(GOLD+"q2_agent_daily_performance")

display(q2_agent_day)

# COMMAND ----------

day1_scoped = spark.read.format("delta").load(SILVER + "day1_scoped")

day2_scoped = spark.read.format("delta").load(SILVER + "day2_scoped")

# COMMAND ----------

# All tickets marked as Resolved (before applying the >15 minute business rule)
day1_all_resolved = day1_scoped.filter(col("status") == "Resolved")

day2_all_resolved = day2_scoped.filter(col("status") == "Resolved")

all_resolved = day1_all_resolved.unionByName(day2_all_resolved)

# Total resolved tickets per Team Lead
resolved_counts = (
    all_resolved
    .groupBy("team_lead_id")
    .agg(count("*").alias("total_marked_resolved"))
)

# Total tickets that qualified after the business rule
qualifying_counts = (
    silver
    .groupBy("team_lead_id")
    .agg(count("*").alias("total_qualifying"))
)

# Compliance percentage
q3_compliance = (
    resolved_counts
    .join(qualifying_counts, on="team_lead_id", how="left")
    .fillna(0, subset=["total_qualifying"])
    .withColumn(
        "compliance_rate_pct",
        spark_round(
            (col("total_qualifying") / col("total_marked_resolved")) * 100,
            2
        )
    )
)

# Save Gold table
q3_compliance.write \
    .format("delta") \
    .mode("overwrite") \
    .save(GOLD + "q3_compliance_rate")

display(q3_compliance)

# COMMAND ----------

profiles = (
    spark.read
    .format("delta")
    .load(BRONZE+"agent_profiles")
    .drop("_ingested_at")
)

# COMMAND ----------

q4_carryover = carryover.select(
    "agent_id",
    "agent_name",
    "team_lead_id",
    "ticket_id",
    "resolution_minutes"
)

q4_carryover.write.format("delta").mode("overwrite").save(GOLD+"q4_carryover_agents")

display(q4_carryover)