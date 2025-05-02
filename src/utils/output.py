import os
from pathlib import Path
from supabase import create_client, Client
import pandas as pd
from openpyxl import load_workbook

from dotenv import load_dotenv
from get_Value import get_value

import numpy as np
from datetime import datetime, timezone


# Initialize the Supabase client
load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL1"),
    os.environ.get("SUPABASE_KEY1")
)
def fill_templates_from_dataframe(dataframe: pd.DataFrame, output_dir = "/workspaces/SolvMate/outputs"):
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
    # Fetch the output mapping data from the Supabase database
    
    response = supabase.table('output_mapping').select('*').execute()
    if not response.data:
        raise ValueError("No mapping data found in the 'outputmapping' table.")

    mapping_data = pd.DataFrame(response.data)

    # Ensure the required columns are present
    required_columns = ['TEMPLATE_NAME', 'DATA_ID', 'CELL']
    if not all(col in mapping_data.columns for col in required_columns):
        raise ValueError(f"The 'outputmapping' table must contain the following columns: {required_columns}")

    # Iterate over all templates
    for template_name in mapping_data['TEMPLATE_NAME'].unique():
        # Load the corresponding template
        template_path = Path(f"/workspaces/SolvMate/templates/{template_name}")
        if not template_path.exists():
            print(f"Template {template_name} not found. Skipping...")
            continue

        workbook = load_workbook(template_path)
        sheet = workbook.active

        # Filter the mapping data for the current template
        template_mapping = mapping_data[mapping_data['TEMPLATE_NAME'] == template_name]

        # Iterate over all `data_id` entries in the mapping
        for data_id in template_mapping['DATA_ID'].values:
            
            cell = template_mapping.loc[template_mapping['DATA_ID'] == data_id, 'CELL'].values[0]
            print(data_id)
            if data_id == 'MKT_INT_DN_A_SH':
                print('GEwonnen')
            else:
                print('')
            
            # Retrieve the value from the DataFrame
            if data_id in dataframe['DATA_ID'].values:
                value = dataframe.loc[dataframe['DATA_ID'] == data_id, 'Value'].values[0]
                
            else:
                value = None  # If no value is found
                print('nsfuhfbh')

            # Write the value into the corresponding cell
            if value is not None:
                sheet[cell] = value
            else:
                print(f"Warning: No value found for data_id {data_id}. Leaving cell {cell} empty.")

        # Save the filled template in the output directory
        output_path = Path(output_dir) / f"Filled_{template_name}"
        workbook.save(output_path)
        print(f"Template {template_name} filled and saved to {output_path}.")


