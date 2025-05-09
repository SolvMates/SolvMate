# Databricks notebook source
# MAGIC %pip install pandas openpyxl
# MAGIC
# MAGIC import pandas as pd
# MAGIC
# MAGIC # Define the path to your Excel file
# MAGIC excel_file_path = "/Volumes/workspace/default/configuration/CORRELATION_MATRIX.xlsx"
# MAGIC
# MAGIC # Read the Excel file using pandas
# MAGIC df = pd.read_excel(excel_file_path)
# MAGIC
# MAGIC # Rename columns
# MAGIC df.columns = [column.replace(" ", "_").replace(",", "_").replace(";", "_").replace("(", "_").replace(")", "_").replace("\n", "_") for column in df.columns]
# MAGIC
# MAGIC # Convert Pandas DataFrame to Spark DataFrame
# MAGIC spark_df = spark.createDataFrame(df)
# MAGIC
# MAGIC # Save the DataFrame as a new table in the "default" schema
# MAGIC spark_df.write \
# MAGIC     .mode("overwrite") \
# MAGIC     .saveAsTable("default.CORRELATION_MATRIX")

# COMMAND ----------

# MAGIC %sql
# MAGIC use catalog `workspace`; select * from `default`.`correlation_matrix` limit 100;