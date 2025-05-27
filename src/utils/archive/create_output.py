
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



# Use the openpyxl engine directly
with pd.ExcelWriter(local_out_path, engine='openpyxl') as writer:
    writer.book = template
    # Write dataframe to excel using template and save in output path
    Output_Enriched2_df.toPandas().to_excel(writer, sheet_name='Output mapping', startrow=12, startcol=2, index=False, header=False)

