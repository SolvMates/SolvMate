# Databricks notebook source
# Install the openpyxl library
%pip install openpyxl

# Import Pandas
import pandas as pd

# Define the path to your Excel file
excel_file_path = "/Volumes/workspace/default/configuration/DATA_ID.xlsx"

# Read the Excel file using Pandas
df = pd.read_excel(excel_file_path)

# Handle non-numeric values in the 'LENGTH' column
df['LENGTH'] = pd.to_numeric(df['LENGTH'], errors='coerce')

# Convert 'DEFAULT_LIST_VALUE' column to string type
df['DEFAULT_LIST_VALUE'] = df['DEFAULT_LIST_VALUE'].astype(str)

# Convert Pandas DataFrame to Spark DataFrame
spark_df = spark.createDataFrame(df)

# Save the DataFrame as a new table in the "default" schema
spark_df.write \
    .mode("overwrite") \
    .saveAsTable("default.DATA_ID")