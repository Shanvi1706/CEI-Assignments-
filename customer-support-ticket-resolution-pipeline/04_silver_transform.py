# Databricks notebook source
dbutils.widgets.text("storage_account", "stsupportpipelineshanvi")

storage_account = dbutils.widgets.get("storage_account")

RAW = f"abfss://raw@{storage_account}.dfs.core.windows.net/"
BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"
SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"
GOLD = f"abfss://gold@{storage_account}.dfs.core.windows.net/"

# COMMAND ----------

storage_account = "stsupportpipelineshanvi"

RAW    = f"abfss://raw@{storage_account}.dfs.core.windows.net/"
BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"
SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"
GOLD   = f"abfss://gold@{storage_account}.dfs.core.windows.net/"

print("Storage paths initialized ✅")

# COMMAND ----------

from pyspark.sql.functions import regexp_extract, col, when, floor

# COMMAND ----------

day1_valid = spark.read.format("delta").load(SILVER + "day1_valid")

day2_valid = spark.read.format("delta").load(SILVER + "day2_valid")

profiles = (
    spark.read
    .format("delta")
    .load(BRONZE + "agent_profiles")
    .drop("_ingested_at")
)

# COMMAND ----------

def add_resolution_minutes(df):

    df = (df
        .withColumn("h", regexp_extract("resolution_time", r"(\d+)h", 1).cast("int"))
        .withColumn("m", regexp_extract("resolution_time", r"(\d+)m", 1).cast("int"))
        .withColumn("s", regexp_extract("resolution_time", r"(\d+)s", 1).cast("int"))
    )

    total_minutes = col("h") * 60 + col("m") + (col("s") / 60)

    df = df.withColumn(
        "resolution_minutes",
        when(col("s") >= 30, floor(total_minutes) + 1)
        .otherwise(floor(total_minutes))
    )

    return df.drop("h", "m", "s")

# COMMAND ----------

day1_timed = add_resolution_minutes(day1_valid)

day2_timed = add_resolution_minutes(day2_valid)

# COMMAND ----------

# Join tickets with agent profiles
day1_joined = day1_timed.join(
    profiles,
    on="agent_id",
    how="left"
)

day2_joined = day2_timed.join(
    profiles,
    on="agent_id",
    how="left"
)

# Keep only Team Leads TL01–TL08
day1_scoped = day1_joined.filter(col("team_lead_id").isin(
    "TL01", "TL02", "TL03", "TL04",
    "TL05", "TL06", "TL07", "TL08"
))

day2_scoped = day2_joined.filter(col("team_lead_id").isin(
    "TL01", "TL02", "TL03", "TL04",
    "TL05", "TL06", "TL07", "TL08"
))

print("Day1 scoped rows:", day1_scoped.count())
print("Day2 scoped rows:", day2_scoped.count())

# COMMAND ----------

day1_scoped.write.format("delta").mode("overwrite").save(SILVER+"day1_scoped")

day2_scoped.write.format("delta").mode("overwrite").save(SILVER+"day2_scoped")

# COMMAND ----------

# Business Rule:
# Keep only resolved tickets that took more than 15 minutes

day1_business = day1_scoped.filter(
    (col("status") == "Resolved") &
    (col("resolution_minutes") > 15)
)

day2_business = day2_scoped.filter(
    (col("status") == "Resolved") &
    (col("resolution_minutes") > 15)
)

print("Day1 business rows:", day1_business.count())
print("Day2 business rows:", day2_business.count())

# COMMAND ----------

day1_business.write.format("delta").mode("overwrite").save(SILVER + "day1_business")

day2_business.write.format("delta").mode("overwrite").save(SILVER + "day2_business")

# COMMAND ----------

# Agents who already qualified on Day 1
day1_success_agents = day1_business.select("agent_id").distinct()

# Keep only Day 2 agents who did NOT qualify on Day 1
day2_after_carryover = day2_business.join(
    day1_success_agents,
    on="agent_id",
    how="left_anti"
)

print("Day2 rows before carry-over filter:", day2_business.count())
print("Day2 rows after carry-over filter:", day2_after_carryover.count())

# Agents removed because they already qualified on Day 1
carryover_agents = day2_business.join(
    day1_success_agents,
    on="agent_id",
    how="left_semi"
)

# COMMAND ----------

day2_after_carryover.write \
    .format("delta") \
    .mode("overwrite") \
    .save(SILVER + "day2_after_carryover")

carryover_agents.write \
    .format("delta") \
    .mode("overwrite") \
    .save(SILVER + "carryover_agents")

# COMMAND ----------

# Combine Day 1 qualified tickets with Day 2 tickets after carry-over rule
silver_combined = day1_business.unionByName(day2_after_carryover)

# Save the final Silver dataset
silver_combined.write \
    .format("delta") \
    .mode("overwrite") \
    .save(SILVER + "combined_qualified_tickets")

# Save carry-over agents
carryover_agents.write \
    .format("delta") \
    .mode("overwrite") \
    .save(SILVER + "carryover_agents")

print("Final Silver row count:", silver_combined.count())