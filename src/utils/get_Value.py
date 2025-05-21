
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

def get_valueExt(target_data_id: str, dataframe, datatyp=None):
    """
    Uses get_value and always returns a single value if possible.
    If datatyp is 'float', converts the value(s) to float.
    """
    data_value = get_value(target_data_id, dataframe)
    # Convert to float if requested
    if datatyp == "float":
        if isinstance(data_value, list):
            data_value = [float(x) if x not in [None, ''] else float('nan') for x in data_value]
            return data_value[0] if len(data_value) == 1 else data_value
        try:
            return float(data_value)
        except Exception:
            return float('nan')
    # Default: return single value if list of length 1, else as is
    if isinstance(data_value, list):
        return data_value[0] if len(data_value) == 1 else data_value
    return data_value

def get_value(target_data_id: str, dataframe):
    # Check if the input is a valid DataFrame
    if not isinstance(dataframe, pd.DataFrame):
        return 'Invalid input: The provided data is not a DataFrame'  # Return an error message if the input is not a DataFrame

    # Check if the target data ID exists in the DataFrame
    if target_data_id in dataframe['DATA_ID'].values:
        # Check if the value is a string (indicating multiple values)
        if isinstance(dataframe.loc[dataframe['DATA_ID'] == target_data_id, 'VALUE'].values[0], str):
            # Split the string into a list of values
            data_list = dataframe.loc[dataframe['DATA_ID'] == target_data_id, 'VALUE'].values[0].split('$$$$')
            return data_list  # Return the list of values
        else:
            # Retrieve a single value
            data_value = dataframe.loc[dataframe['DATA_ID'] == target_data_id, 'VALUE'].values[0]
    else:
        return 'Data id not found'  # Return an error message if the data ID is not found

    return data_value  # Return the retrieved value

