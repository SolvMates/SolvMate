# Databricks notebook source
# MAGIC %pip install pandas openpyxl
# MAGIC
# MAGIC import pandas as pd
# MAGIC from pyspark.sql import SparkSession
# MAGIC from pyspark.sql.functions import udf
# MAGIC from pyspark.sql.types import StringType
# MAGIC
# MAGIC # Initialize Spark session
# MAGIC spark = SparkSession.builder.appName("example").getOrCreate()
# MAGIC
# MAGIC # Step 1: Read the configuration table and filter for WORKSHEET = 'MarketR'
# MAGIC data_id = spark.sql("SELECT * FROM default.data_id WHERE WORKSHEET = 'MarketR'")
# MAGIC
# MAGIC # Step 2: Read the 'MarketR' sheet from the unstructured Excel file
# MAGIC #excel_file_path = "/Volumes/workspace/default/input/MarketR.xlsx" # for test
# MAGIC
# MAGIC excel_file_path = dbutils.widgets.get("input_path") # Parameter set by workflow
# MAGIC df_excel = pd.read_excel(excel_file_path, sheet_name='MarketR', header=None)
# MAGIC
# MAGIC # Step 3: Create a function to extract values based on RC_CODE
# MAGIC def get_cell_value(rc_code):
# MAGIC     if rc_code:
# MAGIC         # Extract the row and column from RC_CODE
# MAGIC         row_num = int(rc_code.split('C')[0][1:])  # Get the number after 'R'
# MAGIC         col_num = int(rc_code.split('C')[1])      # Get the number after 'C'
# MAGIC         
# MAGIC         # Retrieve the value from the DataFrame
# MAGIC         return df_excel.iat[row_num - 1, col_num - 1] if (0 <= row_num - 1 < len(df_excel)) and (0 <= col_num - 1 < len(df_excel.columns)) else None
# MAGIC     return None
# MAGIC
# MAGIC # Register the UDF
# MAGIC get_cell_value_udf = udf(get_cell_value, StringType())
# MAGIC
# MAGIC # Step 4: Create a new column 'VALUE' in data_id
# MAGIC data_id = data_id.withColumn("VALUE", get_cell_value_udf(data_id["RC_CODE"]))
# MAGIC
# MAGIC # Step 5: Store the updated DataFrame as a new table
# MAGIC data_id.write.mode("overwrite").saveAsTable("default.data_id_updated")