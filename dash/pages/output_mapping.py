from dash import Dash, html, dcc, callback, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import dash
import os
from pathlib import Path
from supabase import create_client, Client
import pandas as pd
from openpyxl import load_workbook
from dotenv import load_dotenv
import numpy as np
from datetime import datetime, timezone
import io
import base64

from dash.dcc import send_bytes

import re

load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL1"), os.environ.get("SUPABASE_KEY1")
)

dash.register_page(
    __name__,
    path="/Database/output_mapping_test",
    title="Output mapping",
    name="Output mapping",
    category="Database configuration",
)

# Globale Variable für das zuletzt heruntergeladene DataFrame
last_downloaded_df = None

# Beispiel-Tabelle-Liste
TABLE_OPTIONS = [
    {"label": "Output Mapping", "value": "output_mapping"},
    {"label": "Other Table", "value": "other_table"},
    # weitere Tabellen nach Bedarf
]

def layout():
    """Return the layout for this view"""
    return dbc.Container(
        [
            html.H1("Output Mapping", className="my-4 text-start"),
            html.H2("Upload and Download Mapping", className="mb-3 text-start"),
            html.P(
                "Here you can download the current mapping or upload a new one. "
                "Only the DATA_ID column may be changed. Please follow the instructions in each section.",
                className="text-start mb-4",
            ),
            html.Div([
                html.Label("Select table to update/download:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="table-select",
                    options=TABLE_OPTIONS,
                    value="output_mapping",  # Default
                    clearable=False,
                    style={"width": "300px"}
                ),
            ], className="mb-4"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H3("Download Section"),
                            html.P(
                                "Click the button below to download the current mapping from the database as an Excel file. "
                                "You can use this file as a template for your changes."
                            ),
                            dbc.Button(
                                "Download",
                                id="download-button",
                                color="primary",
                                className="mt-2",
                            ),
                            dcc.Download(id="download-data"),
                        ],
                        width=6,
                        className="border p-3",
                    ),
                    dbc.Col(
                        [
                            html.H3("Upload Section"),
                            html.P(
                                "Upload your modified mapping file here. "
                                "Only files named 'output_mapping.xlsx' are allowed. "
                                "After uploading, press 'Confirm Upload' to apply the changes. "
                                "Note: Only values in the DATA_ID column may be changed. "
                                "Any other changes will be rejected."
                            ),
                            dcc.Upload(
                                id="upload-data",
                                children=html.Button("Upload File"),
                                multiple=False,
                            ),
                            html.Div(id="upload-output", className="mt-3"),
                            dbc.Button(
                                "Confirm Upload",
                                id="upload-button",
                                color="success",
                                className="mt-2",
                                n_clicks=0,
                                disabled=True,
                            ),
                        ],
                        width=6,
                        className="border p-3",
                    ),
                ]
            ),
            html.Hr(),
            html.Div(
                [
                    html.H4("Upload History", className="mt-3"),
                    dbc.Button(
                        "Reload Upload History",
                        id="reload-history-button",
                        color="secondary",
                        className="mb-2 ms-2",
                        n_clicks=0,
                    ),
                    html.Div(
                        id="upload-history",
                        children=[],
                        style={
                            "border": "2px solid #007bff",
                            "borderRadius": "5px",
                            "padding": "10px",
                            "backgroundColor": "#f9f9f9",
                        },
                    ),
                ],
                style={"marginTop": "20px"},
            ),
            dcc.Store(id="upload-file-store", data=None),
        ],
        fluid=True,
        className="py-4",
    )

def render_upload_history():
    response = supabase.table("upload_history").select("*").order("TIME", desc=True).execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        return html.Div("No uploads yet.")
    return html.Ul([
        html.Li(f"{row['TIME']} - {row['NAME']}") for _, row in df.iterrows()
    ])

@callback(
    Output("upload-output", "children"),
    Output("upload-history", "children"),
    Output("upload-button", "disabled"),
    Output("upload-file-store", "data"),
    Input("upload-data", "filename"),
    Input("upload-data", "contents"),
    Input("upload-button", "n_clicks"),
    Input("reload-history-button", "n_clicks"),  # <--- NEU
    State("upload-file-store", "data"),
    State("table-select", "value"),
    prevent_initial_call=True,
)
def handle_upload_and_reload(filename, contents, n_clicks, reload_n_clicks, stored_file, table_name):
    triggered_id = callback_context.triggered[0]["prop_id"].split(".")[0]

    # Reload-Button gedrückt
    if triggered_id == "reload-history-button":
        return dash.no_update, render_upload_history(), dash.no_update, dash.no_update

    # When a file is uploaded
    if triggered_id == "upload-data":
        if filename and contents:
            if filename != "output_mapping.xlsx":
                return (
                    html.Span(
                        "Only files named 'output_mapping.xlsx' are allowed!",
                        style={"color": "red"},
                    ),
                    render_upload_history(),
                    True,
                    None,
                )
            return (
                f"File '{filename}' uploaded successfully! Press 'Confirm Upload' to update the database.",
                render_upload_history(),
                False,
                {"filename": filename, "contents": contents},
            )
        return (
            "",
            render_upload_history(),
            True,
            None,
        )

    # When confirm button is pressed
    if triggered_id == "upload-button" and stored_file:
        filename = stored_file["filename"]
        contents = stored_file["contents"]
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        df_upload = pd.read_excel(io.BytesIO(decoded))

        # Load current mapping from database
        response = supabase.table(table_name).select("*").execute()
        df_db = pd.DataFrame(response.data)

        # Sort and set index for comparison (e.g. by ID)
        df_upload_sorted = df_upload.sort_values(by="ID").reset_index(drop=True)
        df_db_sorted = df_db.sort_values(by="ID").reset_index(drop=True)

        # Check if DataFrames are equal except for DATA_ID
        cols_to_compare = [
            col
            for col in df_upload_sorted.columns
            if col != "DATA_ID" and col in df_db_sorted.columns
        ]
        if not df_upload_sorted[cols_to_compare].equals(df_db_sorted[cols_to_compare]):
            return (
                html.Span(
                    "Error: Only values in the column DATA_ID may be changed!",
                    style={"color": "red"},
                ),
                render_upload_history(),
                True,
                None,
            )

        # Only DATA_ID is different, continue here
        changed_rows = df_upload_sorted[
            df_upload_sorted["DATA_ID"] != df_db_sorted["DATA_ID"]
        ]
        updated_count = 0
        for idx, row in changed_rows.iterrows():
            data_id = row["DATA_ID"]
            if pd.isna(data_id):
                data_id = None
            supabase.table(table_name).update({"DATA_ID": data_id}).eq("ID", row["ID"]).execute()
            updated_count += 1
            print(updated_count)

        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        supabase.table("upload_history").insert({"TIME": upload_time, "NAME": filename}).execute()

        return (
            html.Div([
                html.Span(
                    "Upload successful! Only DATA_ID was changed and the database has been updated.",
                    style={"color": "green"},
                ),
                html.Br(),
                html.Span(f"Total updated entries: {updated_count}", style={"color": "blue"})
            ]),
            render_upload_history(),
            True,
            None,
        )

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@callback(
    Output("download-button", "n_clicks"),
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("table-select", "value"),
    prevent_initial_call=True,
)
def handle_download(n_clicks, table_name):
    global last_downloaded_df
    if n_clicks:
        response = supabase.table(table_name).select("*").execute()
        df = pd.DataFrame(response.data)
        last_downloaded_df = df.copy()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        def write_bytesio(f):
            f.write(output.getvalue())

        return 0, send_bytes(write_bytesio, f"{table_name}.xlsx")
    return dash.no_update, dash.no_update



__all__ = ["layout"]