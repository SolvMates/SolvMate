import os
from pathlib import Path
from supabase import create_client, Client
import pandas as pd
from openpyxl import load_workbook
from dotenv import load_dotenv
from get_Value import get_value
import numpy as np
from datetime import datetime, timezone


import pandas as pd


import re

load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL1"), os.environ.get("SUPABASE_KEY1")
)


def check_cell_value_format(cell_value: str) -> bool:
    # Definiere die regulären Ausdrücke für die Formate
    pattern1 = r"^Z-Z\d{4}$"  # Z-Z0010
    pattern2 = r"^R\d{4}-C\d{4}$"  # R****-C****
    pattern3 = r"^\d{2}R\d{3}-C\d{4}$"  # 33R***-C****
    pattern4 = r"^E\d{4}-C\d{4}$"  # E4010-C1370 und ähnliche

    # Überprüfe, ob cell_value einem der Muster entspricht
    if (
        re.match(pattern1, cell_value)
        or re.match(pattern2, cell_value)
        or re.match(pattern3, cell_value)
        or re.match(pattern4, cell_value)
    ):
        return True
    return False


def read_excel_cells(file_path: str) -> pd.DataFrame:
    # Erstellen eines leeren DataFrames für die Ergebnisse
    results = pd.DataFrame(
        columns=["QRT_ID", "QRT_NAME", "RC_CODE", "CELL_REFERENCE", "DATA_ID", "ID"]
    )

    # Excel-Datei laden
    excel_file = pd.ExcelFile(file_path)

    # Für jedes Worksheet in der Excel-Datei
    for sheet_name in excel_file.sheet_names:
        if sheet_name.startswith("26"):
            print(f"Skipping sheet: {sheet_name}")  # Debugging-Ausgabe
            continue
        df_sheet = excel_file.parse(sheet_name)
        qrt_id = sheet_name[:10].replace(".", "")
        # Durchlaufe alle Zellen im DataFrame
        for row in range(df_sheet.shape[0]):  # Zeilen
            for col in range(df_sheet.shape[1]):  # Spalten
                cell_value = df_sheet.iat[row, col]  # Zelleninhalt

                # Überprüfen, ob der Zelleninhalt dem Zielwert entspricht
                if check_cell_value_format(str(cell_value)):
                    # Zellenposition in Excel-Format (z.B. A1, B2, ...)
                    cell_position = (
                        f"{chr(65 + col)}{row + 2}"  # +2 für menschliche Zählweise
                    )
                    id = f"{sheet_name}_{cell_value}"
                    # Hinzufügen der Informationen zur Ergebnisliste
                    new_row = pd.DataFrame(
                        {
                            "QRT_ID": [qrt_id],
                            "QRT_NAME": [sheet_name],
                            "RC_CODE": [cell_value],
                            "CELL_REFERENCE": [cell_position],
                            "DATA_ID": None,
                            "ID": [id],
                        }
                    )

                    # Hinzufügen der neuen Zeile zum Ergebnis-DataFrame
                    results = pd.concat([results, new_row], ignore_index=True)

    return results


def upsert_data_to_supabase(
    dataframe: pd.DataFrame, table_name: str, unique_column: str
):
    for index, row in dataframe.iterrows():
        # Hier nehmen wir an, dass die Spalte, die die Einträge eindeutig identifiziert, 'unique_column' heißt.
        unique_value = row[unique_column]

        # Überprüfen, ob der Datensatz bereits existiert
        existing_record = (
            supabase.table(table_name)
            .select("*")
            .eq(unique_column, unique_value)
            .execute()
        )

        if existing_record.data:
            # Datensatz existiert, also aktualisieren wir ihn
            supabase.table(table_name).update(row.to_dict()).eq(
                unique_column, unique_value
            ).execute()
            print(f"Updated record with {unique_column}: {unique_value}")
        else:
            # Datensatz existiert nicht, also fügen wir ihn hinzu
            supabase.table(table_name).insert(row.to_dict()).execute()
            print(f"Inserted new record with {unique_column}: {unique_value}")


def create_output_mapping():
    goal_dataframe = read_excel_cells(
        file_path="/workspaces/SolvMate/templates/Output_ERGO.xlsx",
    )
    # create excel file
    upsert_data_to_supabase(goal_dataframe, "output_mapping", "ID")
    output_path = Path("/workspaces/SolvMate/outputs/Output_Mapping.xlsx")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Write the goal_dataframe to the specified sheet
        goal_dataframe.to_excel(
            writer, sheet_name="Goal DataFrame", index=False, header=True
        )


if __name__ == "__main__":
    goal_dataframe = read_excel_cells(
        file_path="/workspaces/SolvMate/templates/Output_ERGO.xlsx",
    )
    # create excel file
    upsert_data_to_supabase(goal_dataframe, "output_mapping", "ID")
    output_path = Path("/workspaces/SolvMate/outputs/Output_Mapping.xlsx")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Write the goal_dataframe to the specified sheet
        goal_dataframe.to_excel(
            writer, sheet_name="Goal DataFrame", index=False, header=True
        )
