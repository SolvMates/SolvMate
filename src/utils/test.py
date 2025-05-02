from input import run_Import
from output import fill_templates_from_dataframe
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import openpyxl
from pathlib import Path
from get_Value import get_value 

def main():
    df = run_Import("/workspaces/SolvMate/input/02.01_SAS_Input_MarketR.xls")
    print(get_value('MKT_INT_DN_A_SH',df))
    fill_templates_from_dataframe(df,)

    return print('done')

main()