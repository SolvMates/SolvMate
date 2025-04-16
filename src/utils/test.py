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
    # Entferne das 'R' und 'C' und extrahiere die Zahlen
    row = int(coord[1:coord.index('C')])  # Zeilennummer
    col = int(coord[coord.index('C') + 1:])  # Spaltennummer
    return [[row, col]]  # Rückgabe als 2D-Liste

def get_value_from_df(df, coord):
    coord_list = convert_coord_to_list(coord)
    row_number = coord_list[0][0] - 1  # Zeilenindex anpassen (0-basiert)
    column_number = coord_list[0][1] - 1  # Spaltenindex anpassen (0-basiert)

    # Überprüfen, ob die Indizes innerhalb der Grenzen des DataFrames liegen
    if row_number < 0 or row_number >= df.shape[0] or column_number < 0 or column_number >= df.shape[1]:
        return "Koordinaten außerhalb des DataFrame-Bereichs"
    
    return df.iloc[row_number, column_number]



    
def load_importdata(input_path: str) -> pd.DataFrame:
    response = (supabase.table('data_id').select('*').eq('WORKSHEET', 'MarketR').execute())
    data_id_table =  pd.DataFrame(response.data)
    data_id_table.insert(1, 'Value', None)

    for id in data_id_table['DATA_ID']:
        sheet_name = data_id_table.loc[data_id_table['DATA_ID'] == id, 'WORKSHEET'].values[0]
        coord = data_id_table.loc[data_id_table['DATA_ID'] == id, 'RC_CODE'].values[0]
        temp_df = pd.read_excel(input_path, sheet_name, header=0, engine='pyxlsb')

        new_value = get_value_from_df(temp_df,coord)
        data_id_table.loc[data_id_table['DATA_ID'] == id, 'Value'] = new_value
     
    return data_id_table.head(100)

               
def main():
    input_path = Path("/workspaces/SolvMate/input/02.01_SAS_Input_MarketR.xlsb")
    return print(load_importdata(input_path))



main()



      


