from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash

# pages/E2E_run_test.py
dash.register_page(
    __name__,
    path="/End-to-End/Start-calculation",
    title='Start calculation',
    name='Start calculation',
    category='End-to-End'
)

def layout():
    """Return the layout for this view"""
    return dbc.Container([
        html.H1("SolvMate End-to-End test", className="my-4"),
        dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Specify a path to an input file of version v30 or later:", className="fw-bold mb-2"),
                            dcc.Upload(
                                id="file-path-input",
                                children=dbc.Button("Select File", color="secondary", className="mb-3"),
                                multiple=False,
                                className="mb-3"
                            ),
                            html.Div(id="selected-filename", className="mb-2 text-secondary"),
                            dbc.Label("Short description:", className="fw-bold mb-2"),
                            dbc.Input(
                                id="description-input",
                                type="text",
                                placeholder="Enter a short description for this run",
                                className="mb-3"
                            ),
                            dbc.Label("Scope of run:", className="fw-bold mb-2"),
                            dbc.Select(
                                id="scope-input",
                                options=[
                                    {"label": "SCR, MCR", "value": "SCR, MCR"},
                                    {"label": "Risk margin only", "value": "Risk margin only"}
                                ],
                                value="SCR, MCR",
                                className="mb-3"
                            ),
                        ], width=12)
                    ]),
                    dbc.Button(
                        "Start calculation",
                        id="start-calculation-button",
                        color="primary",
                        className="mb-4",
                        size="md",
                        n_clicks=0
                    ),
                    dbc.Spinner(html.Div(id="download-area_e2e"), size="md", color="primary", fullscreen=False)
                ], className="mt-3"),
                html.Div(id="status-area_e2e", className="mt-3")
        ], fluid=True, className="py-4")

# --- Backend logic ---
import base64
import tempfile
import importlib
from dash import ctx
import sys
sys.path.insert(0, "/workspaces/SolvMate")
from datetime import datetime, timezone
from src.utils import output
from dotenv import load_dotenv
import os
load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
from supabase import create_client, Client
supabase = None
if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)

from dash.dependencies import Output, Input, State
import random

@callback(
    [
        Output("status-area_e2e", "children"),
        Output("start-calculation-button", "disabled"),
        Output("start-calculation-button", "children"),
        Output("download-area_e2e", "children"),
        Output("selected-filename", "children")
    ],
    [
        Input("start-calculation-button", "n_clicks"),
        Input("file-path-input", "filename")
    ],
    [
        State("file-path-input", "contents"),
        State("file-path-input", "filename"),
        State("description-input", "value"),
        State("scope-input", "value")
    ],
    prevent_initial_call=True
)
def handle_start_calculation(n_clicks, uploaded_filename, file_contents, file_name, description, scope):
    ctx_triggered = ctx.triggered_id if hasattr(ctx, 'triggered_id') else None
    filename_display = f"Selected file: {uploaded_filename}" if uploaded_filename else "No file selected."
    if ctx_triggered == "file-path-input":
        # Only update filename display
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, filename_display
    if not file_contents or not file_name:
        return dbc.Alert("Please select an input file.", color="warning"), False, "Start calculation", None, filename_display
    if not description or not description.strip():
        return dbc.Alert("Please enter a description before running.", color="warning"), False, "Start calculation", None, filename_display
    # Save uploaded file to a temp location
    content_type, content_string = file_contents.split(',')
    decoded = base64.b64decode(content_string)
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[-1]) as temp_file:
        temp_file.write(decoded)
        temp_input_path = temp_file.name
    # Log run in Supabase
    run_id = random.randint(1, 1000000)
    start_time = datetime.now(timezone.utc)
    run_data = {
        "run_id": run_id,
        "short_description": description,
        "run_start": start_time.isoformat(),
        "run_status": "running",
        "scope_of_run": scope,
        "user_id": os.environ.get("USER", "unknown")
    }
    if supabase is not None:
        supabase.table("run_status").insert(run_data).execute()
    # Import and run calculation
    try:
        solvmate_main = importlib.import_module("src.solvmate_main")
        solvmate_main.run_calculation(temp_input_path, run_id)
        # Find output file (assuming output.fill_QRT_from_dataframe writes to run_output_path)
        output_dir = os.path.join("/workspaces/SolvMate/outputs", str(run_id))
        # Find the first .xlsx file in output_dir
        output_file = None
        for f in os.listdir(output_dir):
            if f.endswith(".xlsx"):
                output_file = os.path.join(output_dir, f)
                break
        if output_file:
            # Prepare download link
            with open(output_file, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            download_button = dcc.Download(id="download-output-e2e")
            download_link = html.A(
                "Download Output",
                id="download-link-e2e",
                download=os.path.basename(output_file),
                href=f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{encoded}",
                target="_blank",
                className="btn btn-success mt-3"
            )
            status = dbc.Alert(f"Run completed successfully. Results saved in: {output_file}", color="success")
            return status, False, "Start calculation", download_link, filename_display
        else:
            status = dbc.Alert("Run finished, but no output file was found.", color="warning")
            return status, False, "Start calculation", None, filename_display
    except Exception as e:
        update_run_status = getattr(importlib.import_module("src.solvmate_main"), "update_run_status")
        update_run_status(run_id, "failed", datetime.now(timezone.utc))
        status = dbc.Alert(f"Error during run: {str(e)}", color="danger")
        return status, False, "Start calculation", None, filename_display

# Make layout available at module level
__all__ = ['layout']
