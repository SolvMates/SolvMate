import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

# Initialize Spark session
spark = SparkSession.builder.appName("example").getOrCreate()

# Step 1: Read the configuration table and filter for WORKSHEET = 'MarketR'
data_id = spark.sql("SELECT * FROM default.data_id WHERE WORKSHEET = 'MarketR'")

# Step 2: Read the 'MarketR' sheet from the unstructured Excel file
#excel_file_path = "/Volumes/workspace/default/input/MarketR.xlsx" # for test

#excel_file_path = dbutils.widgets.get("input_path") # Parameter set by workflow
#df_excel = pd.read_excel(excel_file_path, sheet_name='MarketR', header=None)

# Step 3: Create a function to extract values based on RC_CODE
def get_cell_value(rc_code):
    if rc_code:
        # Extract the row and column from RC_CODE
        row_num = int(rc_code.split('C')[0][1:])  # Get the number after 'R'
        col_num = int(rc_code.split('C')[1])      # Get the number after 'C'
        
        # Retrieve the value from the DataFrame
        return df_excel.iat[row_num - 1, col_num - 1] if (0 <= row_num - 1 < len(df_excel)) and (0 <= col_num - 1 < len(df_excel.columns)) else None
    return None

# Register the UDF
get_cell_value_udf = udf(get_cell_value, StringType())

# Step 4: Create a new column 'VALUE' in data_id
data_id = data_id.withColumn("VALUE", get_cell_value_udf(data_id["RC_CODE"]))

# Step 5: Store the updated DataFrame as a new table
data_id.write.mode("overwrite").saveAsTable("default.data_id_updated")