# Databricks notebook source
#TODO: Add to init.py
%pip install pandas openpyxl


import pandas as pd
from pyspark.sql import SparkSession
import numpy as np
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

# Initialize Spark session
spark = SparkSession.builder.appName("example").getOrCreate()

# Define the path to your Excel file
excel_file_path = "/Volumes/workspace/default/configuration/Output_Mapping.xlsx"

# Read the Excel file 
df = pd.read_excel(
    excel_file_path, 
    sheet_name='Output mapping', 
    usecols="C:K", 
    skiprows=11, 
    nrows=52
) 
# Read range 'Output mapping'!C12:K63

# Rename columns to remove invalid characters "" ,;{}()\n\t=""
df.columns = [
    str(column).replace(" ", "")
               .replace(",", "_")
               .replace(";", "_")
               .replace("(", "_")
               .replace(")", "_")
               .replace("\n", "_")
    for column in df.columns
]

# Convert Pandas DataFrame to Spark DataFrame
spark_df = spark.createDataFrame(df)

# Save the DataFrame as a new table in the "default" schema
spark_df.write \
    .mode("overwrite") \
    .saveAsTable("default.Output_Mapping2")

# COMMAND ----------

# MAGIC %md
# MAGIC Here is the ERGOGPT prompt that created the basis for the following code:
# MAGIC
# MAGIC **PROMPT**:
# MAGIC
# MAGIC
# MAGIC The table "default.Output_Mapping" contains a matrix of output cells, where the columns "C00*0" ("C0020", ..., "C0080") are the column numbers and the values in column "Row" ("R0100", ..., "R0800") are the row numbers of the cells. The column "ROW_ID" specifies the order of the rows. Each of the output cells contains a mapping logic, that reference either variables in table "defaul.data_id_updated", where column "DATA_ID" contains the variable name, and column "VALUE" contains the variable value, or variables in table "default.aggregation_tree_market_enriched", where column "_NODE_ID" contains the variable name, and column "VALUE" contains the variable value.
# MAGIC
# MAGIC Can you please write a python script for databricks, which does the following:
# MAGIC 1. Read in tables "default.Output_Mapping", "defaul.data_id_updated" and "default.aggregation_tree_market_enriched" as data frames.
# MAGIC 2. Create a new data frame, that has the same columns as table Output_Mapping, but the values in the columns "C0020", ..., "C0080" are replaced with the values from the variable in tables "defaul.data_id_updated" and "default.aggregation_tree_market_enriched" using the respective mapping logic in "default.Output_Mapping". Here, the leading table for the variable values must be "default.aggregation_tree_market_enriched". If this table does not contain the variable, then "defaul.data_id_updated" should be searched. If both values do not contain the variables, then the respective output cell should retain its mapping rule as a value.
# MAGIC 3. Save this new data frame as table "default.Output_Enriched".
# MAGIC 4. Write the data frame into the .xlsx template "/FileStore/tables/Output_Mapping-2.xlsx" into range "'Output mapping'!C12:K63".
# MAGIC

# COMMAND ----------

# Import necessary libraries
from pyspark.sql import functions as F

# Step 1: Read in the tables as data frames
output_mapping_df = spark.table("default.Output_Mapping2")
data_id_updated_df = spark.table("default.data_id_updated")
aggregation_tree_df = spark.table("default.aggregation_tree_market_enriched")

# Step 2: Create a new data frame with enriched values
# Create a mapping dictionary for aggregation_tree_market_enriched
aggregation_dict = {row["_NODE_ID"]: row["VALUE"] for row in aggregation_tree_df.collect()}
# Create a mapping dictionary for data_id_updated
data_id_dict = {row["DATA_ID"]: row["VALUE"] for row in data_id_updated_df.collect()}

# Combine both dictionaries
combined_dict = {**aggregation_dict, **data_id_dict}

# Create a UDF to replace values based on the mapping logic
replace_udf = F.udf(lambda value: combined_dict.get(value, value), StringType())

# Apply the UDF to each relevant column
for col_name in [f"C00{i}" for i in range(20, 81, 10)]:  # C0020, C0040, C0060, C0080
    output_mapping_df = output_mapping_df.withColumn(col_name, replace_udf(F.col(col_name)))

# Save the Spark DataFrame as a new table in the "default" schema
output_mapping_df.write \
    .mode("overwrite") \
    .saveAsTable("default.Output_Enriched2")

# COMMAND ----------

# MAGIC %md
# MAGIC In the next part, we are wrinting the dataframe above into a copy of the output template that is located under /Volumes/workspace/default/output/Output_Template.xlsx and save it in a folder /Volumes/workspace/default/output/output_{run_id}/
# MAGIC where run_id is some increasing integer, which we later write into our status table.
# MAGIC
# MAGIC For this, we are using the following tutorials:
# MAGIC - Writing dataframes into an excel template: https://jingwen-z.github.io/writing-dataframes-into-an-excel-template/
# MAGIC - Writing excel files into Unity Catalog volumes: 
# MAGIC     - https://learn.microsoft.com/en-us/azure/databricks/dev-tools/sdk-python#files-in-volumes
# MAGIC     - https://docs.databricks.com/en/files/volumes.html
# MAGIC     - https://chenhirsh.com/working-with-excel-files-in-databricks/ 
# MAGIC

# COMMAND ----------

# DBTITLE 1,Export Spark DataFrame to Excel Template - First try with to_excel()
#CAN BE DELETED LATER

# # Install the xlsxwriter module
# %pip install xlsxwriter

# # Import necessary libraries
# import pyspark.pandas as ps
# import pandas as pd
# from pyspark.sql import SparkSession

# # Initialize Spark session
# spark = SparkSession.builder.appName("OutputMappingEnrichment").getOrCreate()

# # Step 1: Read in the tables as data frames
# Output_Enriched2_df = spark.table("default.Output_Enriched2")

# # Step 4: Write the data frame to the specified Excel template
# output_file_path = "/Volumes/workspace/default/output/Output.xlsx"

# # Write the data frame to the specified Excel template using openpyxl
# Output_Enriched2_df.toPandas().to_excel(output_file_path, startrow=11, startcol=2, index=False, header=False)
# """


# """
# writer = pd.ExcelWriter(output_file_path, engine='xlsxwriter')
# enriched_ps_df.to_pandas().to_excel(writer, sheet_name='Output mapping', startrow=11, startcol=2, index=False, header=False)
# wb = writer.book
# ws = writer.sheets['Output mapping']
# writer.save()


# COMMAND ----------

# DBTITLE 1,Export Spark DataFrame to Excel Template - Second try with to_excel()
#CAN BE DELETED LATER

# # Install the xlsxwriter module
# %pip install xlsxwriter

# # Import necessary libraries
# import pyspark.pandas as ps
# import pandas as pd
# from pyspark.sql import SparkSession

# # Initialize Spark session
# spark = SparkSession.builder.appName("OutputMappingEnrichment").getOrCreate()

# # Step 1: Read in the tables as data frames
# Output_Enriched2_df = spark.table("default.Output_Enriched2")

# # Step 4: Write the data frame to the specified Excel template
# output_file_path = "/Volumes/workspace/default/output/Output_Template.xlsx"

# writer = pd.ExcelWriter(output_file_path, engine='xlsxwriter')
# Output_Enriched2_df.toPandas().to_excel(writer, sheet_name='Output mapping', startrow=11, startcol=2, index=False, header=False)
# wb = writer.book
# ws = writer.sheets['Output mapping']
# writer.save()


# COMMAND ----------

# DBTITLE 1,Export Spark DataFrame to Excel Template - Second try with to_excel() to dbfs (should not be used, since dbfs is legacy)
#CAN BE DELETED LATER

# # Install the xlsxwriter module
# %pip install xlsxwriter

# # Import necessary libraries
# import pyspark.pandas as ps
# import pandas as pd
# from pyspark.sql import SparkSession
# import os

# # Initialize Spark session
# spark = SparkSession.builder.appName("OutputMappingEnrichment").getOrCreate()

# # Step 1: Read in the tables as data frames
# Output_Enriched2_df = spark.table("default.Output_Enriched2")

# # Step 4: Write the data frame to the specified Excel template
# output_file_path = "dbfs:/tmp/Output_Template.xlsx"

# # Create the directory if it does not exist
# os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# df1 = Output_Enriched2_df.to_pandas_on_spark()
# df1.to_excel(output_file_path)

# COMMAND ----------


#CAN BE DELETED LATER

# #CODE EXAMPLE FROM https://learn.microsoft.com/en-us/azure/databricks/dev-tools/sdk-python#files-in-volumes
# #EXAMPLE WAS ADJUSTED AS NEEDED

# from databricks.sdk import WorkspaceClient
# from datetime import datetime

# w = WorkspaceClient()

# # Define volume, folder, and file details.
# catalog            = 'workspace'
# schema             = 'default'
# volume             = 'output'
# volume_path        = f"/Volumes/{catalog}/{schema}/{volume}" # /Volumes/main/default/my-volume

# current_time = datetime.now().strftime("%S:%M:%H")
# volume_folder   = f"output_{current_time}"
# volume_folder_path = f"{volume_path}/{volume_folder}" # /Volumes/main/default/my-volume/my-folder

# volume_file        = f"Output_{current_time}.xlsx"

# volume_file_path   = f"{volume_folder_path}/{volume_file}" # /Volumes/main/default/my-volume/my-folder/data.csv


# #upload_file_path   = './data.csv' #NOT NEEDED HERE

# # Create an empty folder in a volume.
# w.files.create_directory(volume_folder_path)

# #NOT NEEDED NOW
# # # Upload a file to a volume.
# # with open(upload_file_path, 'rb') as file:
# #   file_bytes = file.read()
# #   binary_data = io.BytesIO(file_bytes)
# #   w.files.upload(volume_file_path, binary_data, overwrite = True)



# # List the contents of a volume.
# for item in w.files.list_directory_contents(volume_path):
#   print(item.path)

# # List the contents of a folder in a volume.
# for item in w.files.list_directory_contents(volume_folder_path):
#   print(item.path)

# #NOT NEEDED HERE
# # # Print the contents of a file in a volume.
# # resp = w.files.download(volume_file_path)
# # print(str(resp.contents.read(), encoding='utf-8'))

# # # Delete a file from a volume.
# # w.files.delete(volume_file_path)

# # # Delete a folder from a volume.
# # w.files.delete_directory(volume_folder_path)





# COMMAND ----------

#INIT

%pip install pandas openpyxl
%pip install xlsxwriter --upgrade

dbutils.library.restartPython()

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import pandas as pd
from datetime import datetime
import openpyxl
import string
import pyspark.pandas as ps
from shutil import move
from pyspark.sql import SparkSession

w = WorkspaceClient()

# Define volume, folder, and file details.
catalog            = 'workspace'
schema             = 'default'
volume             = 'output'
volume_path        = f"/Volumes/{catalog}/{schema}/{volume}" # /Volumes/main/default/my-volume

#RUN_ID = 001 # For test purposes; If the script is run by workflow, this is set as a parameter
RUN_ID = dbutils.widgets.get("run_id")
volume_folder   = f"output_{RUN_ID}"
volume_folder_path = f"{volume_path}/{volume_folder}" # /Volumes/main/default/my-volume/my-folder
volume_file        = f"Output_{RUN_ID}.xlsx"
volume_file_path   = f"{volume_folder_path}/{volume_file}" # /Volumes/main/default/

# Create an empty folder in a volume.
w.files.create_directory(volume_folder_path)

# Initialize Spark session
spark = SparkSession.builder.appName("test").getOrCreate()

# Read in the tables as data frames
Output_Enriched2_df = spark.table("default.Output_Enriched2")

#Load template
template_file = f"{volume_path}/Output_Template.xlsx"
template = openpyxl.load_workbook(template_file)

#Create a writer
out_path = 'dbfs:/tmp/output.xlsx' #workaround using dbfs

# Use the openpyxl engine directly
with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
    writer.book = template
    # Write dataframe to excel using template and save in output path
    Output_Enriched2_df.toPandas().to_excel(writer, sheet_name='Output mapping', startrow=12, startcol=2, index=False, header=False)

# The new workbook is now saved in the output path dbfs:/tmp/output.xlsx
# Now copy the output file into the volume:

# Create an empty folder in a volume.
w.files.create_directory(volume_folder_path)
move('dbfs:/tmp/output.xlsx',f"{volume_file_path}")
dbutils.fs.ls(f"{volume_file_path}")