"""
This script processes data from Excel files and integrates it with a Supabase database. 
It extracts, transforms, and combines data from multiple worksheets into a single pandas DataFrame. 
The processed data is then exported to an Excel file for further use.

Modules:
--------
- os: For accessing environment variables.
- dotenv: To load environment variables from a `.env` file.
- supabase: For interacting with the Supabase database.
- pandas: For data manipulation and analysis.
- numpy: For numerical operations.
- datetime: For working with date and time.
- openpyxl: For writing data to Excel files.
- pathlib: For handling file paths.
- get_Value: A custom module for retrieving specific values from a DataFrame.

Environment Setup:
------------------
- The script uses environment variables for Supabase credentials:
  - `SUPABASE_URL`: The URL of the Supabase instance.
  - `SUPABASE_KEY`: The API key for accessing the Supabase database.
- These variables are loaded using the `dotenv` module.

Supabase Client Initialization:
-------------------------------
- The `supabase` client is created using the `create_client` function from the `supabase` module.
- This client is used to interact with the Supabase database for fetching and processing data.

Imports:
--------
- The script imports necessary libraries and modules for database interaction, data manipulation, and file handling.
- The `get_value` function from the `get_Value` module is used to retrieve specific values from a DataFrame.

Functions:
----------
1. convert_coord_to_list(coord):
   - Converts an Excel-style coordinate (e.g., `R1C1`) into a list of row and column indices.
   - **Parameters**:
     - `coord` (str): The coordinate string.
   - **Returns**:
     - A list containing the row and column indices.

2. get_value_from_df(df, coord):
   - Retrieves a value from a pandas DataFrame based on a given coordinate.
   - **Parameters**:
     - `df` (pd.DataFrame): The DataFrame to retrieve the value from.
     - `coord` (str or list): The coordinate of the value.
   - **Returns**:
     - The value at the specified coordinate or an error message if the coordinate is out of bounds.

3. convert_excel_range_to_list(coord_range):
   - Converts an Excel-style range (e.g., `R1C1:R3C3`) into a list of all coordinates within the range.
   - **Parameters**:
     - `coord_range` (str): The range string.
   - **Returns**:
     - A list of all coordinates within the range.

4. load_importdata(input_path: str, target_worksheet=None) -> pd.DataFrame:
   - Loads data from a Supabase table and an Excel worksheet, processes it, and returns a pandas DataFrame.
   - **Parameters**:
     - `input_path` (str): Path to the input Excel file.
     - `target_worksheet` (str): The name of the worksheet to process.
   - **Returns**:
     - A pandas DataFrame containing the processed data.

5. run_Import(worksheets: list = [...]) -> pd.DataFrame:
   - Processes multiple worksheets from an Excel file and combines them into a single DataFrame.
   - **Parameters**:
     - `worksheets` (list): A list of worksheet names to process.
   - **Returns**:
     - A combined pandas DataFrame containing data from all worksheets.

6. main():
   - Executes the entire workflow:
     - Processes data from multiple worksheets.
     - Retrieves specific values from the processed DataFrame.
     - Exports the final DataFrame to an Excel file.
   - **Returns**:
     - The final pandas DataFrame.

"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import openpyxl
from pathlib import Path
from get_Value import get_value 

load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)
def convert_coord_to_list(coord):
    # Convert R..C..Code to Coordinates
    row = int(coord[1:coord.index('C')])  # Extract the row number from the coordinate string (e.g., "R1C1" -> 1)
    col = int(coord[coord.index('C') + 1:])  # Extract the column number from the coordinate string (e.g., "R1C1" -> 1)
    return [[row, col]]  # Return the coordinates as a list containing row and column indices

def get_value_from_df(df, coord):
    if isinstance(coord, str):  # Check if the coordinate is a string
        coord_list = convert_coord_to_list(coord)  # Convert the string coordinate to a list of row and column indices
    else:
        coord_list = [coord]  # If already a list, wrap it in another list for consistency
     
    row_number = coord_list[0][0] - 2  # Adjust the row index to be zero-based (DataFrame indexing starts at 0)
    column_number = coord_list[0][1] - 1  # Adjust the column index to be zero-based

    # Check if the row or column index is out of bounds for the DataFrame
    if row_number < 0 or row_number >= df.shape[0] or column_number < 0 or column_number >= df.shape[1]:
        return "Coordinates out of DataFrame bounds"  # Return an error message if the indices are invalid
    
    return df.iloc[row_number, column_number]  # Retrieve the value from the DataFrame at the specified row and column

def convert_excel_range_to_list(coord_range):
    # Split the coordinate range into start and end coordinates
    parts = coord_range.split(':')
    start_coord = parts[0]  # Extract the starting coordinate (e.g., "R1C1")
    end_coord = parts[1]  # Extract the ending coordinate (e.g., "R3C3")
    
    # Check if a step value is provided
    step = 1  # Default step value
    if len(parts) == 3:
        step = int(parts[2])  # Extract the step value if provided (e.g., "R1C1:R3C3:2")
    
    # Extract row and column indices from the start coordinate
    start_row = int(start_coord[1:start_coord.index('C')])  # Extract the row number from the start coordinate
    start_col = int(start_coord[start_coord.index('C') + 1:])  # Extract the column number from the start coordinate
    
    # Extract row and column indices from the end coordinate
    end_row = int(end_coord[1:end_coord.index('C')])  # Extract the row number from the end coordinate
    end_col = int(end_coord[end_coord.index('C') + 1:])  # Extract the column number from the end coordinate
    
    # Initialize a list to store all coordinates in the range
    coordinates = []
    
    # Generate all coordinates within the range
    for row in range(start_row, end_row + 1, step):  # Iterate over rows with the specified step
        for col in range(start_col, end_col + 1):  # Iterate over columns
            coordinates.append([row, col])  # Append each coordinate as a list [row, col]
    
    return coordinates  # Return the list of coordinates

def load_importdata(input_path: str, target_worksheet=None) -> pd.DataFrame:
    # Initialize an empty DataFrame to store data from Supabase
    data_id_table = pd.DataFrame()
    offset = 0  # Offset for pagination
    limit = 1000  # Number of rows to fetch per request

    while True:
        # Fetch data from the Supabase table 'data_id' with pagination
        response = (supabase.table('data_id')
                    .select('*')
                    .eq('WORKSHEET', target_worksheet)  # Filter by the target worksheet
                    .range(offset, offset + limit - 1)  # Fetch rows within the specified range
                    .execute())
        
        # Convert the response data to a DataFrame
        temp_df = pd.DataFrame(response.data)
        if temp_df.empty:
            break  # Exit the loop if no more data is available
        
        # Append the fetched data to the main DataFrame and remove duplicates
        data_id_table = pd.concat([data_id_table, temp_df]).drop_duplicates(subset='DATA_ID', keep='first', ignore_index=True)
        offset += limit  # Increment the offset for the next request

    # Add a new column 'Value' to store the extracted values
    
    data_id_table.insert(1, 'Value', None)
    i = 0  # Counter for debugging purposes
    
    # Load the Excel worksheet into a DataFrame
    temp_df = pd.read_excel(input_path, target_worksheet, header=0, engine='pyxlsb')
    for id in data_id_table['DATA_ID']:
        print(i)  # Print the counter for debugging
        i += 1
        # Get the coordinate associated with the current data ID
        coord = data_id_table.loc[data_id_table['DATA_ID'] == id, 'RC_CODE'].values[0]
        # Check if the worksheet matches the target worksheet
        if target_worksheet == data_id_table.loc[data_id_table['DATA_ID'] == id, 'WORKSHEET'].values[0]:
            if id.endswith('*'):  # Check if the data ID ends with '*'                
                Value_list = []  # Initialize a list to store values
                coord_list = convert_excel_range_to_list(coord)  # Convert the range to a list of coordinates
                
                # Retrieve values for each coordinate in the range
                for coordinate in coord_list:
                    new_value = get_value_from_df(temp_df, coordinate)
                    if str(new_value) == 'nan' or new_value == 'Coordinates out of DataFrame bounds':
                        print('')        
                    else:
                        Value_list.append(new_value)
                        
                # Join the values with '$$$$' and store them in the DataFrame
                new_value = '$$$$'.join(map(str, Value_list))
                data_id_table.loc[data_id_table['DATA_ID'] == id, 'Value'] = new_value
            else:
                # Retrieve a single value and store it in the DataFrame
                new_value = get_value_from_df(temp_df, coord)
                if data_id_table.loc[data_id_table['DATA_ID'] == id, 'DEFAULT_LIST_VALUE'].values[0] != None:
                   
                    if new_value == None:
                        data_id_table.loc[data_id_table['DATA_ID'] == id, 'Value'] = data_id_table.loc[data_id_table['DATA_ID'] == id, 'DEFAULT_LIST_VALUE'].values[0]
                    elif str(new_value) == 'nan':
                        data_id_table.loc[data_id_table['DATA_ID'] == id, 'Value'] = data_id_table.loc[data_id_table['DATA_ID'] == id, 'DEFAULT_LIST_VALUE'].values[0]
                    else:
                        if id == 'INFO_REPORT_DT':
                            new_value = pd.to_datetime(new_value, unit='D', origin='1900-04-01')
                        data_id_table.loc[data_id_table['DATA_ID'] == id, 'Value'] = new_value             
                else:
                    if id == 'INFO_REPORT_DT':
                        new_value = pd.to_datetime(new_value, unit='D', origin='1900-04-01')
                    data_id_table.loc[data_id_table['DATA_ID'] == id, 'Value'] = new_value
    return data_id_table  # Return the processed DataFrame

def run_Import(input_path="/workspaces/SolvMate/input/02.01_SAS_Input_MarketR.xlsb", worksheets=['Basic input', 'MarketR', 'ConcR', 'CurrR', 'CDR', 'CDR - SCR hyp', 'net Prem CP', 'LnH SLT UW', 'Health cat', 'NL NatCat', 'NatC OthR', 'NL man-made', 'OpRisk', 'MCR', 'Simplifications']):
    input_p = Path(input_path)  # Convert the input path to a Path object

    # Check if the input path exists and is a file
    if not input_p.exists() or not input_p.is_file():
        raise FileNotFoundError(f"Invalid input path: {input_path}. Please provide a valid file path.")

    dataframes = []  # Initialize an empty list to store DataFrames

    # Process each worksheet
    for worksheet in worksheets:
        data_id_table = load_importdata(input_p, worksheet)  # Load data for the worksheet
        dataframes.append(data_id_table)  # Append the DataFrame to the list

    # Combine all DataFrames into a single DataFrame
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(combined_df)  # Print the combined DataFrame for debugging
    return combined_df  # Return the combined DataFrame

def main():
    goal_dataframe = run_Import()
    print(goal_dataframe.head(20))
    print(get_value('CPD_NL_EXPPV_FP_EX_R13_S10_***',goal_dataframe ))
    #create excel file
    output_path = Path("/workspaces/SolvMate/outputs/Output_ImportData.xlsx")
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
         #Write the goal_dataframe to the specified sheet
         goal_dataframe.to_excel(
            writer,
            sheet_name='Goal DataFrame',
            index=False,
            header=True
         )
    return goal_dataframe

main()  # Execute the main function






