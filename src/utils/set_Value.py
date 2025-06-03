import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import openpyxl
from pathlib import Path


def set_value(target_data_id: str, dataframe, value=None):
    # Check if the input is a valid DataFrame
    if not isinstance(dataframe, pd.DataFrame):
        return "Invalid input: The provided data is not a DataFrame"  # Return an error message if the input is not a DataFrame

    # Check if the target data ID exists in the DataFrame
    if target_data_id in dataframe["DATA_ID"].values:
        # If a value is provided, set it in the DataFrame or else set it to None
        if value is not None:
            dataframe.loc[dataframe["DATA_ID"] == target_data_id, "VALUE"] = value
        else:
            dataframe.loc[dataframe["DATA_ID"] == target_data_id, "VALUE"] = None

        # Return the updated DataFrame
        return dataframe
    else:
        return (
            "Data ID not found"  # Return an error message if the data ID is not found
        )
