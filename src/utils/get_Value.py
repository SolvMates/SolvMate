
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import openpyxl
from pathlib import Path
"""
get_value(target_data_id: str, dataframe) -> Union[str, list, Any]

This function retrieves the value(s) associated with a specific data ID from a pandas DataFrame. 
It supports both single values and multiple values (separated by "$$$$") and validates the input to ensure it is a DataFrame.

Parameters:
-----------
- target_data_id (str): 
    The unique identifier for the data to be retrieved from the DataFrame.

- dataframe (pd.DataFrame): 
    The pandas DataFrame containing the data. It must have at least the following columns:
    - 'DATA_ID': The column containing unique identifiers for the data.
    - 'Value': The column containing the corresponding values.

Returns:
--------
- Union[str, list, Any]: 
    - A list of values if the 'Value' column contains multiple values separated by "$$$$".
    - A single value if the 'Value' column contains a single value.
    - An error message (str) if the input is invalid or the data ID is not found.

Error Handling:
---------------
- If the input is not a valid pandas DataFrame, the function returns:
    'Invalid input: The provided data is not a DataFrame'.
- If the target data ID is not found in the 'DATA_ID' column, the function returns:
    'Data id not found'.

Example:
--------
# Example DataFrame
data = {
    'DATA_ID': ['ID_1', 'ID_2', 'ID_3'],
    'Value': ['Value1$$$$Value2', 'Value3', 'Value4']
}
df = pd.DataFrame(data)

# Retrieve multiple values
get_value('ID_1', df)
# Output: ['Value1', 'Value2']

# Retrieve a single value
get_value('ID_2', df)
# Output: 'Value3'

# Handle missing data ID
get_value('ID_4', df)
# Output: 'Data id not found'

# Handle invalid input
get_value('ID_1', 'not_a_dataframe')
# Output: 'Invalid input: The provided data is not a DataFrame'
"""

load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

def get_value(target_data_id: str, dataframe):
    
    # Check if the input is a valid DataFrame
    if not isinstance(dataframe, pd.DataFrame):
        return 'Invalid input: The provided data is not a DataFrame'  # Return an error message if the input is not a DataFrame
    
    # Check if the target data ID exists in the DataFrame
    if target_data_id in dataframe['DATA_ID'].values:
        # Check if the value is a string (indicating multiple values)
        if isinstance(dataframe.loc[dataframe['DATA_ID'] == target_data_id, 'Value'].values[0], str):
            # Split the string into a list of values
            data_list = dataframe.loc[dataframe['DATA_ID'] == target_data_id, 'Value'].values[0].split('$$$$')
            return data_list  # Return the list of values
        else:
            # Retrieve a single value
            data_value = dataframe.loc[dataframe['DATA_ID'] == target_data_id, 'Value'].values[0]
            
    else:
       
        for id in dataframe['DATA_ID'].values:
            
            
            if id == target_data_id:              
                data_value = dataframe.loc[dataframe['DATA_ID'] == id, 'Value'].values[0]
                
                break
            
        return 'Data id not found'  # Return an error message if the data ID is not found
    # Check if the value is a string (indicating multiple values)
    return data_value  # Return the retrieved value

