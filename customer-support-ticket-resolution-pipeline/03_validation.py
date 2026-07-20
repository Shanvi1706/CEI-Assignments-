# Databricks notebook source
dbutils.widgets.text("storage_account", "stsupportpipelineshanvi")

storage_account = dbutils.widgets.get("storage_account")

RAW = f"abfss://raw@{storage_account}.dfs.core.windows.net/"
BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"
SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"
GOLD = f"abfss://gold@{storage_account}.dfs.core.windows.net/"

# COMMAND ----------

storage_account = "stsupportpipelineshanvi"

BRONZE = f"abfss://bronze@{storage_account}.dfs.core.windows.net/"
SILVER = f"abfss://silver@{storage_account}.dfs.core.windows.net/"

# COMMAND ----------

day1_bronze = spark.read.format("delta").load(BRONZE + "day1_tickets")
day2_bronze = spark.read.format("delta").load(BRONZE + "day2_tickets")

def split_valid_invalid(df, name):
    invalid = df.filter(
        df.ticket_id.isNull() | df.agent_id.isNull() | df.resolution_time.isNull()
    )
    valid = df.filter(
    df.ticket_id.isNotNull() &
    df.agent_id.isNotNull() &
    df.resolution_time.isNotNull()
)
    print(f"{name}: {valid.count()} valid rows, {invalid.count()} invalid rows dropped")
    return valid, invalid

day1_valid, day1_invalid = split_valid_invalid(day1_bronze, "Day1")
day2_valid, day2_invalid = split_valid_invalid(day2_bronze, "Day2")

#keep a record of what you dropped and why - good pipeline hygiene
day1_valid.write.format("delta").mode("overwrite").save(SILVER + "day1_valid")
day2_valid.write.format("delta").mode("overwrite").save(SILVER + "day2_valid")

# Keep a record of what you dropped and why — good pipeline hygiene
day1_invalid.write.format("delta").mode("overwrite").save(SILVER + "day1_rejected")
day2_invalid.write.format("delta").mode("overwrite").save(SILVER + "day2_rejected")