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

5. run_import(worksheets: list = [...]) -> pd.DataFrame:
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
import logging
from typing import List, Union, Dict, Optional, Any, Tuple


# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class SupabaseDataImporter:
    def run_import(
        self,
        input_path="/workspaces/SolvMate/input/02.01_SAS_Input_MarketR.xls",
        worksheets=[
            "Basic input",
            "MarketR",
            "ConcR",
            "CurrR",
            "CDR",
            "CDR - SCR hyp",
            "net Prem CP",
            "LnH SLT UW",
            "Health cat",
            "NL NatCat",
            "NatC OthR",
            "NL man-made",
            "OpRisk",
            "MCR",
            "Simplifications",
        ],
    ) -> pd.DataFrame:
        input_p = Path(input_path)  # Convert the input path to a Path object

        # Check if the input path exists and is a file
        if not input_p.exists() or not input_p.is_file():
            raise FileNotFoundError(
                f"Invalid input path: {input_path}. Please provide a valid file path."
            )

        dataframes = []  # Initialize an empty list to store DataFrames

        # Process each worksheet
        for worksheet in worksheets:
            data_id_table = self._load_importdata(
                input_p, worksheet
            )  # Load data for the worksheet
            dataframes.append(data_id_table)  # Append the DataFrame to the list

        # Combine all DataFrames into a single DataFrame
        combined_df = pd.concat(dataframes, ignore_index=True)
        return combined_df  # Return the combined DataFrame

    def get_dataframe(
        self, data_id_enriched: pd.DataFrame, table_id: str
    ) -> pd.DataFrame:
        # Get all the requiered data_id ranges and store them in a list.
        column_data_ids = data_id_enriched.loc[
            data_id_enriched["TABLE_ID"] == table_id, "DATA_ID"
        ].tolist()
        help_list = []
        # Get every data_id of each range and store them in a list and store this list in a list.
        for column_id in column_data_ids:
            column_id = column_id.rstrip("*")
            filtered_data_ids = data_id_enriched[
                data_id_enriched["DATA_ID"].str.startswith(column_id)
            ]
            data_id_list = filtered_data_ids["DATA_ID"].tolist()
            help_list.append(data_id_list)
            biggest_element = 0
            index = 0
        # Look for the biggest data_id in each list and save the index of the biggest element.
        for sublist in help_list:

            current_data_id = column_data_ids[index]
            last_element = sublist[-1]
            if not last_element.endswith("*"):
                n = len(current_data_id.rstrip("*"))
                last_element = int(last_element[n:])

                if last_element > biggest_element:
                    biggest_element = last_element
            index = index + 1
        # Create the column names with the name of the data_id ranges and add the column INDEX.
        rows = []
        column_names = []
        for id_names in column_data_ids:
            column_names.append(id_names.rstrip("*"))
        columns = ["INDEX"]
        columns.extend(column_names)
        # Create each row of the dataframe in a loop, in each iteration loop over every data_id_range list to get the right value of the data_id.
        for row_i in range(biggest_element + 1):
            row = []
            row.append(row_i)
            for sublist in help_list:
                right_data_id = None
                value_for_right_data_id = None
                for data_id in sublist:
                    if data_id.endswith("_" + str(row_i)):
                        right_data_id = data_id
                        value_for_right_data_id = data_id_enriched.loc[
                            data_id_enriched["DATA_ID"] == right_data_id, "VALUE"
                        ].values[0]
                row.append(value_for_right_data_id)
            rows.append(row)
        result_dataframe = pd.DataFrame(rows, columns=columns)

        return result_dataframe

    def _convert_coord_to_list(self, coord: str) -> List[List[int]]:
        """
        Convert Excel-style coordinate to list of coordinates.

        Args:
            coord: Excel coordinate string (e.g., 'R1C1')

        Returns:
            List containing [row, col] indices
        """
        try:
            c_index = coord.index("C")
            row = int(coord[1:c_index])
            col = int(coord[c_index + 1 :])
            return [[row, col]]
        except (ValueError, IndexError) as e:
            logger.error(f"Invalid coordinate format: {coord}")
            raise ValueError(f"Invalid coordinate format: {coord}") from e

    def _get_value_from_df(self, df: pd.DataFrame, coord: Union[str, List[int]]) -> Any:
        """
        Get value from DataFrame using Excel-style coordinates or [row, col] list.

        Args:
            df: Source DataFrame
            coord: Excel coordinate string or [row, col] list

        Returns:
            Value from the DataFrame at the specified position
        """
        try:
            coord_list = (
                self._convert_coord_to_list(coord)
                if isinstance(coord, str)
                else [coord]
            )
            row_idx = int(coord_list[0][0]) - 2
            col_idx = int(coord_list[0][1]) - 1

            if (0 <= row_idx < df.shape[0]) and (0 <= col_idx < df.shape[1]):
                return df.iloc[row_idx, col_idx]
            return None

        except Exception as e:
            logger.error(f"Error getting value from DataFrame: {str(e)}")
            return None

    def _convert_excel_range_to_list(self, coord_range: str) -> List[List[int]]:
        """
        Convert Excel-style range to list of coordinates.

        Args:
            coord_range: Excel range string (e.g., 'R1C1:R3C3')

        Returns:
            List of [row, col] coordinate pairs
        """
        try:
            parts = coord_range.split(":")
            if len(parts) < 2:
                raise ValueError(f"Invalid range format: {coord_range}")

            start_coord = self._convert_coord_to_list(parts[0])[0]
            end_coord = self._convert_coord_to_list(parts[1])[0]
            step = int(parts[2]) if len(parts) > 2 else 1

            coordinates = [
                [row, col]
                for row in range(start_coord[0], end_coord[0] + 1, step)
                for col in range(start_coord[1], end_coord[1] + 1)
            ]

            return coordinates

        except Exception as e:
            logger.error(f"Error converting range to coordinates: {str(e)}")
            raise

    def _load_importdata(
        self, input_path: Union[str, Path], target_worksheet: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load and process data from an Excel file based on configuration from Supabase.

        Args:
            input_path: Path to the input Excel file
            target_worksheet: Name of the worksheet to process

        Returns:
            DataFrame containing the processed data
        """
        if not isinstance(input_path, (str, Path)):
            raise TypeError("input_path must be a string or Path object")

        if target_worksheet is None:
            raise ValueError("target_worksheet must be specified")

        input_path = Path(input_path) if isinstance(input_path, str) else input_path

        try:
            # Fetch all data at once
            response = (
                supabase.table("data_id")
                .select("*")
                .eq("WORKSHEET", target_worksheet)
                .execute()
            )

            data_id_table = pd.DataFrame(response.data)
            if "TABLE_ID" not in data_id_table.columns:
                data_id_table["TABLE_ID"] = pd.NA
            if data_id_table.empty:
                logger.warning(
                    f"No configuration found for worksheet: {target_worksheet}"
                )
                # Ensure TABLE_ID column exists even if DataFrame is empty
                data_id_table = pd.DataFrame(
                    columns=list(response.data[0].keys()) if response.data else []
                )
                if "TABLE_ID" not in data_id_table.columns:
                    data_id_table["TABLE_ID"] = pd.NA
                return data_id_table

            # Remove duplicates immediately
            data_id_table = data_id_table.drop_duplicates(
                subset="DATA_ID", keep="first"
            )
            data_id_table.insert(1, "VALUE", None)

            # Load Excel data
            try:
                if input_path.suffix == ".xlsb":
                    df = pd.read_excel(
                        input_path,
                        sheet_name=target_worksheet,
                        header=0,
                        engine="pyxlsb",
                    )
                elif input_path.suffix == ".xls":
                    df = pd.read_excel(
                        input_path, sheet_name=target_worksheet, header=0, engine="xlrd"
                    )
                else:
                    raise ValueError(
                        f"Unsupported file format: {input_path}. Only .xlsb and .xls files are supported."
                    )
            except Exception as e:
                logger.error(
                    f"Error reading worksheet {target_worksheet} from {input_path}: {str(e)}"
                )
                raise

            # Create a fast lookup dictionary for values
            value_map: Dict[Tuple[int, int], Any] = {}
            for row_idx in range(len(df)):
                for col_idx in range(len(df.columns)):
                    val = df.iloc[row_idx, col_idx]
                    if pd.notna(val):
                        value_map[(row_idx + 2, col_idx + 1)] = val

            # Process data IDs efficiently
            for idx, row in data_id_table.iterrows():
                data_id = str(row["DATA_ID"])
                coord = str(row["RC_CODE"])

                try:
                    if data_id.endswith("*"):
                        # Handle range of values
                        coord_list = self._convert_excel_range_to_list(coord)

                        i = 0
                        for c in coord_list:
                            val = value_map.get((c[0], c[1]))
                            new_data_id = data_id.rstrip("*") + str(i)
                            new_row = row.copy()
                            if new_row["TYPE"] == "C":
                                new_row["VALUE"] = str(val)
                            elif new_row["TYPE"] == "N" and val is not None:
                                new_row["VALUE"] = float(val)
                            new_row["DATA_ID"] = new_data_id
                            new_row["TABLE_ID"] = 0
                            if pd.notna(val):
                                data_id_table = pd.concat(
                                    [data_id_table, pd.DataFrame([new_row])],
                                    ignore_index=True,
                                )
                            i = i + 1

                    else:
                        # Handle single value
                        coord_list = self._convert_coord_to_list(coord)[0]
                        val = value_map.get((coord_list[0], coord_list[1]))

                        if pd.notna(val):
                            if (
                                data_id == "INFO_REPORT_DT"
                                and input_path.suffix == ".xlsb"
                            ):
                                try:
                                    val = pd.Timestamp("1899-12-30") + pd.Timedelta(
                                        days=int(val)
                                    )
                                except:
                                    logger.warning(
                                        f"Could not convert date value for {data_id}: {val}"
                                    )
                            if data_id_table.at[idx, "TYPE"] == "C":
                                val = str(val)
                            elif data_id_table.at[idx, "TYPE"] == "N":
                                try:
                                    val = float(val)
                                except:
                                    val = val
                            data_id_table.at[idx, "VALUE"] = val
                        elif (
                            pd.notna(row.get("DEFAULT_LIST_VALUE"))
                            and row.get("DEFAULT_LIST_VALUE") != ""
                        ):
                            if data_id_table.at[idx, "TYPE"] == "C":
                                data_id_table.at[idx, "VALUE"] = str(
                                    row["DEFAULT_LIST_VALUE"]
                                )
                            elif data_id_table.at[idx, "TYPE"] == "N":
                                data_id_table.at[idx, "VALUE"] = float(
                                    row["DEFAULT_LIST_VALUE"]
                                )
                        else:
                            data_id_table.drop(idx, inplace=True)

                except Exception as e:
                    logger.error(f"Error processing {data_id} at {coord}: {str(e)}")
                    continue

            # After all processing, ensure TABLE_ID column exists
            if "TABLE_ID" not in data_id_table.columns:
                data_id_table["TABLE_ID"] = pd.NA
            return data_id_table

        except Exception as e:
            logger.error(f"Error in load_importdata: {str(e)}")
            raise


if __name__ == "__main__":
    supabase_data_importer = SupabaseDataImporter()
    goal_dataframe = supabase_data_importer.run_import(
        "/workspaces/SolvMate/input/04.01_SAS_Input_CDR.xls"
    )
    testvar = supabase_data_importer.get_dataframe(goal_dataframe, "CPTY_TYPE1")
    # create excel file
    output_path = Path("/workspaces/SolvMate/outputs/Output_ImportData.xlsx")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Write the goal_dataframe to the specified sheet
        goal_dataframe.to_excel(
            writer, sheet_name="Goal DataFrame", index=False, header=True
        )
