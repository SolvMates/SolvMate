import os
from pathlib import Path
from supabase import create_client, Client
import pandas as pd
from openpyxl import load_workbook
from input import run_Import
from dotenv import load_dotenv
from get_Value import get_value

import numpy as np
from datetime import datetime, timezone


# Initialize the Supabase client
load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL1"), os.environ.get("SUPABASE_KEY1")
)


def fill_templates_from_dataframe(
    dataframe: pd.DataFrame, output_dir="/workspaces/SolvMate/outputs"
):
    """
    Fills Excel templates based on the mapping defined in the Supabase database.

    Parameters:
    -----------
    - dataframe (pd.DataFrame): The DataFrame containing `data_id` and `value` pairs.
    - output_dir (str): The directory where the filled templates will be saved.

    Returns:
    --------
    None
    """
    # Ensure the input DataFrame has a column named 'DATA_ID'
    if "DATA_ID" not in dataframe.columns:
        if "NODE_ID" in dataframe.columns:
            dataframe = dataframe.rename(columns={"NODE_ID": "DATA_ID"})
        else:
            raise ValueError(
                "The input DataFrame must contain a column named 'DATA_ID' or 'NODE_ID'."
            )
    # Fetch the output mapping data from the Supabase database

    mapping_data = pd.DataFrame()
    offset = 0  # Offset for pagination
    limit = 1000  # Number of rows to fetch per request

    while True:
        # Fetch data from the Supabase table 'data_id' with pagination
        response = (
            supabase.table("output_mapping")
            .select("*")
            .range(offset, offset + limit - 1)  # Fetch rows within the specified range
            .execute()
        )

        # Convert the response data to a DataFrame
        temp_df = pd.DataFrame(response.data)
        if temp_df.empty:
            break  # Exit the loop if no more data is available

        # Append the fetched data to the main DataFrame and remove duplicates
        mapping_data = pd.concat([mapping_data, temp_df])
        offset += limit  # Increment the offset for the next request

    # Load the template file
    template_path = Path(f"/workspaces/SolvMate/templates/Output_ERGO.xlsx")
    workbook = load_workbook(template_path)

    # Iterate over all worksheets in the workbook
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        if sheet_name.startswith("26") == True:
            print(f"Skipping sheet: {sheet_name}")  # Skip sheets starting with "26"
            continue
        # Filter the mapping data for the current worksheet
        worksheet_mapping = mapping_data[mapping_data["QRT_NAME"] == sheet_name]
        # Iterate over all `data_id` entries in the mapping
        for id in worksheet_mapping["ID"].values:
            cell = worksheet_mapping.loc[
                worksheet_mapping["ID"] == id, "CELL_REFERENCE"
            ].values[0]
            data_id = worksheet_mapping.loc[
                worksheet_mapping["ID"] == id, "DATA_ID"
            ].values[0]
            found = False
            value = None
            if type(data_id) == str:
                data_id = data_id.strip()
            for data_id_from_dataframe in dataframe["DATA_ID"].values:
                if data_id_from_dataframe == data_id:
                    value = get_value(data_id, dataframe)
                    print(f"Found value for data_id {data_id}: {value}")
                    found = True
                    break
            if found == False:
                print(
                    "Warning: No value found for data_id {data_id}. Leaving cell {cell} empty."
                )

            # Write the value into the corresponding cell

            if value is not None:
                if type(value) == list:
                    sheet[cell] = value[0]
                else:
                    try:
                        # Convert the value to a float if possible
                        value = float(value)
                        sheet[cell] = value
                    except ValueError:
                        # If conversion fails, write the value as a string
                        sheet[cell] = str(value)

    # Save the filled template in the output directory
    output_path = Path(output_dir) / f"Filled_Output_ERGO.xlsx"
    workbook.save(output_path)
    print(f"Template filled and saved to {output_path}.")


def run_output(dataframe: pd.DataFrame):
    fill_templates_from_dataframe(dataframe)


if __name__ == "__main__":
    # Example DataFrame with `data_id` and `value` pairs

    dataframe = run_Import("/workspaces/SolvMate/input/02.01_SAS_Input_MarketR.xls")

    # Fill the templates based on the DataFrame
    fill_templates_from_dataframe(dataframe)
