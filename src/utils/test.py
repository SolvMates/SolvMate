"""
This script provides utility functions for processing data from Excel files and interacting with a Supabase database.
It includes functions for coordinate conversion, data extraction from Excel ranges, and loading data into a pandas DataFrame.

Modules:
--------
- os: For accessing environment variables.
- dotenv: To load environment variables from a .env file.
- supabase: For interacting with the Supabase database.
- pandas: For data manipulation and analysis.
- numpy: For numerical operations.
- datetime: For working with date and time.
- openpyxl: For working with Excel files.
- pathlib: For handling file paths.

Functions:
----------
1. convert_coord_to_list(coord):
    Converts a coordinate string (e.g., "R1C1") into a list of row and column indices.

2. get_value_from_df(df, coord):
    Retrieves a value from a pandas DataFrame based on a given coordinate.

3. convert_excel_range_to_list(coord_range):
    Converts an Excel range (e.g., "R1C1:R3C3") into a list of all coordinates within the range.

4. load_importdata(input_path: str, target_worksheet=None) -> pd.DataFrame:
    Loads data from a Supabase table and an Excel file, processes it, and returns a pandas DataFrame.

5. get_value(target_data_id: str, dataframe):
    Retrieves the value(s) associated with a specific data ID from a pandas DataFrame.

6. main():
    Main function to load data from multiple worksheets, combine them into a single DataFrame, and retrieve specific values.

Usage:
------
- Ensure the `.env` file contains the `SUPABASE_URL` and `SUPABASE_KEY` environment variables.
- Place the input Excel file in the specified path.
- Call the `main()` function to execute the script.

Notes:
------
- The script uses the `pyxlsb` engine for reading Excel files in binary format.
- The `load_importdata` function handles pagination for large datasets from Supabase.
- The `get_value` function supports retrieving multiple values separated by "$$$$" for ranges.

Example:
--------
1. Convert a coordinate string to a list:
    `convert_coord_to_list("R1C1")` -> `[[1, 1]]`

2. Extract a value from a DataFrame:
    `get_value_from_df(df, [[1, 1]])` -> Returns the value at row 0, column 0.

3. Load data from an Excel file and Supabase:
    `load_importdata("/path/to/file.xlsb", "Sheet1")` -> Returns a DataFrame with processed data.

4. Retrieve a value by data ID:
    `get_value("FX_LOCAL_CCY", dataframe)` -> Returns the value(s) for the given data ID.

"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import openpyxl
from pathlib import Path


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
                print('***')  # Debugging output
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

def get_value(target_data_id: str, dataframe):
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
        return 'Data id not found'  # Return an error message if the data ID is not found

    return data_value  # Return the retrieved value

def run_Import():
    # List of worksheet names to process ['Basic input','MarketR','ConcR','CurrR','CDR','CDR - SCR hyp','net Prem CP','LnH SLT UW','Health cat','NL NatCat','NatC OthR','NL nam-made','OpRisk','MCR','Simplifications']
    worksheets = ['Basic input','MarketR','ConcR','CurrR','CDR','CDR - SCR hyp','net Prem CP','LnH SLT UW','Health cat','NL NatCat','NatC OthR','NL man-made','OpRisk','MCR','Simplifications']
    dataframes = []  # List to store DataFrames for each worksheet
    input_path = Path("/workspaces/SolvMate/input/02.01_SAS_Input_MarketR.xlsb")  # Path to the input Excel file
    
    # Process each worksheet
    for worksheet in worksheets:
        data_id_table = load_importdata(input_path, worksheet)  # Load data for the worksheet
        dataframes.append(data_id_table)  # Append the DataFrame to the list
    
    # Combine all DataFrames into a single DataFrame
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(combined_df)  # Print the combined DataFrame for debugging
    return combined_df  # Return the combined DataFrame

def main():
    goal_dataframe = run_Import()
    print(goal_dataframe.head(20))
    print(get_value('INFO_REPORT_DT',goal_dataframe ))
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






