# Databricks notebook source
# MAGIC %pip install pandas openpyxl
# MAGIC
# MAGIC import pandas as pd
# MAGIC from pyspark.sql import SparkSession
# MAGIC
# MAGIC # Initialize Spark session
# MAGIC spark = SparkSession.builder.appName("example").getOrCreate()
# MAGIC
# MAGIC # Define the path to your Excel file
# MAGIC excel_file_path = "/Volumes/workspace/default/configuration/aggregation_tree_market.xlsx"
# MAGIC
# MAGIC # Read the Excel file into a Pandas DataFrame
# MAGIC df = pd.read_excel(excel_file_path)
# MAGIC
# MAGIC # Rename columns in the Pandas DataFrame
# MAGIC df.columns = [column.replace(" ", "_")
# MAGIC                      .replace(",", "_")
# MAGIC                      .replace(";", "_")
# MAGIC                      .replace("(", "_")
# MAGIC                      .replace(")", "_")
# MAGIC                      .replace("\n", "_") 
# MAGIC               for column in df.columns]
# MAGIC
# MAGIC # Convert the Pandas DataFrame to a Spark DataFrame
# MAGIC spark_df = spark.createDataFrame(df)
# MAGIC
# MAGIC # Save the Spark DataFrame as a new table in the "default" schema
# MAGIC spark_df.write \
# MAGIC     .mode("overwrite") \
# MAGIC     .option("mergeSchema", "true") \
# MAGIC     .saveAsTable("default.aggregation_tree_market")

# COMMAND ----------

# MAGIC %sql
# MAGIC use catalog `workspace`; select * from `default`.`aggregation_tree_market` limit 100;

# COMMAND ----------

# MAGIC %md
# MAGIC The following table aggregation_tree_market contains input for a market SCR calculation (without currency and concentration risk) in Solvency II in form of an aggregation tree structure, where column _NODE_ID
# MAGIC contains all nodes of the tree, column _PARENT_NODE_ID contains their respective parent node and AGGREGATION_METHOD_CD contains either the value "external", which means that the input of the value is provided externally via a variable (column DATA_ID) in table "data_id_updated", or one of the following aggregation methods:
# MAGIC -  "sum": The value for this node is calculated as a sum of all child nodes
# MAGIC -  "max": The value for this node is calculated as the maximum of all child nodes
# MAGIC -  "correlated": The value for this node is calculated with the help of a correlation matrix. The name of the matrix to be used in the aggregation is given in column _MATRIX_ID. The values of all correlation matrices are stored in table default.correlation_matrix, which consists of the following columns: 
# MAGIC -- CORRELATION_MATRIX_ID: ID of correlation matrix, which is referenced in aggregation_tree_market._MATRIX_ID
# MAGIC -- VAR1_NM: ID of variable 1
# MAGIC -- VAR2_NM: ID of variable 2
# MAGIC -- CORRELATION_VALUE_NO: Correlation value
# MAGIC The resulting aggregation logic using "correlated is: sqrt(sum(Corr_i,j*Node_i*Node_j)) over all child nodes of the respective node.
# MAGIC - "dnav": All child nodes of a node with aggregation method "dnav" are either assets or liabilities. This information is specified in column "BS_TYPE" with "asset" for assets and "liab" for liabilities. Each asset or liability has a scenario that is specified in column "SCENARIO": "BC" is the base case and "SH" is the shocked scenario. With this information, the aggregation logic for "dnav" is: (Sum of all base case assets - sum of all base case liabilities) - ((Sum of all shocked assets - sum of all shocked liabilities)).
# MAGIC - "max_scen": Does the same as "max" for now.
# MAGIC
# MAGIC Can you please write a method, that takes the input "aggregation_tree_id" and does the following steps: 
# MAGIC 1. Read in the tables "aggregation_tree" and "data_id_updated" as data frames.
# MAGIC 2. Add the column "VALUE" to the data frame "aggregation_tree".
# MAGIC 3. For the specified "aggregation_tree_id", read in all values for all nodes with "_AGGREGATION_METHOD_CD" = "external" from data frame "data_id_updated", where _NODE_ID = DATA_ID in "data_id_updated".
# MAGIC 4. Aggregate all other values using their aggregation method, which is definded in column "AGGREGATION_METHOD_CD".
# MAGIC 5. Save the results in a new table in schema "default" with name "aggregation_tree_market_enriched".
# MAGIC
# MAGIC