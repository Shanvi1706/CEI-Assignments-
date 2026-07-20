# Databricks notebook source
dbutils.widgets.text("storage_account", "stsupportpipelineshanvi")

storage_account = dbutils.widgets.get("storage_account")

RAW = f"abfss://raw@{storage_account}.dfs.core.windows.net/"
BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"
SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"
GOLD = f"abfss://gold@{storage_account}.dfs.core.windows.net/"

# COMMAND ----------

# Storage paths
storage_account = "stsupportpipelineshanvi"

RAW    = f"abfss://raw@{storage_account}.dfs.core.windows.net/"
BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"
SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"
GOLD   = f"abfss://gold@{storage_account}.dfs.core.windows.net/"

print("Storage paths initialized ✅")

# COMMAND ----------

storage_account = "stsupportpipelineshanvi"

BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"

dbutils.fs.mkdirs(BRONZE + "test_folder")

display(dbutils.fs.ls(BRONZE))

# COMMAND ----------

from pyspark.sql.functions import lit, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType

ticket_schema = StructType([
    StructField("ticket_id", StringType(), True),
    StructField("agent_id", StringType(), True),
    StructField("status", StringType(), True),
    StructField("resolution_time", StringType(), True),
])

profile_schema = StructType([
    StructField("agent_id", StringType(), True),
    StructField("agent_name", StringType(), True),
    StructField("role", StringType(), True),
    StructField("team_lead_id", StringType(), True),
])

day1_raw = (
    spark.read
    .option("header", True)
    .schema(ticket_schema)
    .csv(RAW + "day1_tickets")
    .withColumn("day", lit(1))
    .withColumn("_ingested_at", current_timestamp())
)

day2_raw = (
    spark.read
    .option("header", True)
    .schema(ticket_schema)
    .csv(RAW + "day2_tickets")
    .withColumn("day", lit(2))
    .withColumn("_ingested_at", current_timestamp())
)

profiles_raw = (
    spark.read
    .option("header", True)
    .schema(profile_schema)
    .csv(RAW + "agent_profiles")
    .withColumn("_ingested_at", current_timestamp())
)

day1_raw.write.format("delta").mode("overwrite").save(BRONZE + "day1_tickets")
day2_raw.write.format("delta").mode("overwrite").save(BRONZE + "day2_tickets")
profiles_raw.write.format("delta").mode("overwrite").save(BRONZE + "agent_profiles")

print("Day1 count:", day1_raw.count())
print("Day2 count:", day2_raw.count())
print("Profiles count:", profiles_raw.count())