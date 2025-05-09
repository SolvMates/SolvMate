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
    os.environ.get("SUPABASE_URL1"),
    os.environ.get("SUPABASE_KEY1")
)


dash.register_page(
    __name__,
    path="/Database/output_mapping_test",
    title='Output mapping',
    name='Output mapping',
    category='Database configuration'
)

# Liste zur Speicherung der Upload-Historie (global)
upload_history = []

# Globale Variable für das zuletzt heruntergeladene DataFrame
last_downloaded_df = None

def layout():
    """Return the layout for this view"""
    return dbc.Container([
        html.H1("Output Mapping", className="my-4 text-start"),
        html.H2("Upload and Download Mapping", className="mb-3 text-start"),
        html.P(
            "Here you can download the current mapping or upload a new one. "
            "Only the DATA_ID column may be changed. Please follow the instructions in each section.",
            className="text-start mb-4"
        ),
        dbc.Row([
            dbc.Col([
                html.H3("Download Section"),
                html.P(
                    "Click the button below to download the current mapping from the database as an Excel file. "
                    "You can use this file as a template for your changes."
                ),
                dbc.Button("Download", id="download-button", color="primary", className="mt-2"),
                dcc.Download(id="download-data"),
            ], width=6, className="border p-3"),
            dbc.Col([
                html.H3("Upload Section"),
                html.P(
                    "Upload your modified mapping file here. "
                    "Only files named 'output_mapping.xlsx' are allowed. "
                    "After uploading, press 'Confirm Upload' to apply the changes. "
                    "Note: Only values in the DATA_ID column may be changed. "
                    "Any other changes will be rejected."
                ),
                dcc.Upload(
                    id='upload-data',
                    children=html.Button('Upload File'),
                    multiple=False
                ),
                html.Div(id='upload-output', className='mt-3'),
                dbc.Button("Confirm Upload", id="upload-button", color="success", className="mt-2", n_clicks=0, disabled=True),
            ], width=6, className="border p-3"),
        ]),
        html.Hr(),
        html.Div([
            html.H4("Upload History", className="mt-3"),
            html.Div(id='upload-history', children=[], style={
                "border": "2px solid #007bff", "borderRadius": "5px",
                "padding": "10px", "backgroundColor": "#f9f9f9"
            })
        ], style={"marginTop": "20px"}),
        dcc.Store(id="upload-file-store", data=None),
    ], fluid=True, className="py-4")

@callback(
    Output("upload-output", "children"),
    Output("upload-history", "children"),
    Output("upload-button", "disabled"),
    Output("upload-file-store", "data"),
    Input("upload-data", "filename"),
    Input("upload-data", "contents"),
    Input("upload-button", "n_clicks"),
    State("upload-file-store", "data"),
    prevent_initial_call=True
)
def handle_upload(filename, contents, n_clicks, stored_file):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    global upload_history

    # When a file is uploaded
    if triggered_id == "upload-data":
        if filename and contents:
            if filename != "output_mapping.xlsx":
                return (
                    html.Span("Only files named 'output_mapping.xlsx' are allowed!", style={"color": "red"}),
                    html.Ul([html.Li(f"{name} - {date}") for name, date in upload_history]),
                    True,
                    None
                )
            return (
                f"File '{filename}' uploaded successfully! Press 'Confirm Upload' to update the database.",
                html.Ul([html.Li(f"{name} - {date}") for name, date in upload_history]),
                False,
                {"filename": filename, "contents": contents}
            )
        return "", html.Ul([html.Li(f"{name} - {date}") for name, date in upload_history]), True, None

    # When confirm button is pressed
    if triggered_id == "upload-button" and stored_file:
        filename = stored_file["filename"]
        contents = stored_file["contents"]
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df_upload = pd.read_excel(io.BytesIO(decoded))

        # Load current mapping from database
        response = supabase.table("output_mapping").select("*").execute()
        df_db = pd.DataFrame(response.data)

        # Sort and set index for comparison (e.g. by ID)
        df_upload_sorted = df_upload.sort_values(by="ID").reset_index(drop=True)
        df_db_sorted = df_db.sort_values(by="ID").reset_index(drop=True)

        # Check if DataFrames are equal except for DATA_ID
        cols_to_compare = [col for col in df_upload_sorted.columns if col != "DATA_ID" and col in df_db_sorted.columns]
        if not df_upload_sorted[cols_to_compare].equals(df_db_sorted[cols_to_compare]):
            return (
                html.Span("Error: Only values in the column DATA_ID may be changed!", style={"color": "red"}),
                html.Ul([html.Li(f"{name} - {date}") for name, date in upload_history]),
                True,
                None
            )

        # --- Only DATA_ID is different, continue here ---
        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        upload_history.append((filename, upload_time))
        history_display = html.Ul([
            html.Li(f"{name} - {date}") for name, date in upload_history
        ])
        return (
            html.Span("Upload successful! Only DATA_ID was changed.", style={"color": "green"}),
            history_display,
            True,
            None
        )

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@callback(
    Output("download-button", "n_clicks"),
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    prevent_initial_call=True
)
def handle_download(n_clicks):
    global last_downloaded_df
    if n_clicks:
        response = supabase.table("output_mapping").select("*").execute()
        df = pd.DataFrame(response.data)
        last_downloaded_df = df.copy()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        def write_bytesio(f):
            f.write(output.getvalue())
        return 0, send_bytes(write_bytesio, "output_mapping.xlsx")
    return dash.no_update, dash.no_update

# Make layout available at module level
__all__ = ['layout']
