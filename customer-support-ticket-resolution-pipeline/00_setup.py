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

print("Connected ✅")

# COMMAND ----------

display(dbutils.fs.ls(RAW))

# COMMAND ----------

storage_account = "stsupportpipelineshanvi"

RAW = f"abfss://raw@{storage_account}.dfs.core.windows.net/"

display(dbutils.fs.ls(RAW))