from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash

# pages/E2E_run_test.py
dash.register_page(
    __name__,
    path="/End-to-End/End-to-End",
    title='End-to-End test',
    name='End-to-End test',
    category='End-to-End'
)

def layout():
    """Return the layout for this view"""
    return dbc.Container([
        html.H1("SolvMate End-to-End test", className="my-4"),
        dbc.Tabs([
            dbc.Tab(label="Perform calculation", tab_id="perform-calculation", children=[
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
            ], className="p-3"),
            # Log tab removed
            dbc.Tab(label="Run Status Table", tab_id="run-status-table", children=[
                html.Div(id="run-status-table-container", className="p-3")
            ], className="p-3")
        ], id="tabs", active_tab="perform-calculation", className="mb-4")
    ], fluid=True, className="py-4")

# --- Run Status Table Callback ---
import pandas as pd



@callback(
    Output("run-status-table-container", "children"),
    Input("tabs", "active_tab")
)
def update_run_status_table(active_tab):
    if active_tab != "run-status-table":
        return dash.no_update
    # Query Supabase for run_status table
    if supabase is None:
        return dbc.Alert("Supabase credentials are missing. Please set SUPABASE_URL and SUPABASE_KEY.", color="danger")
    # try block removed (no except/finally)
    data = supabase.table("run_status").select("*").order("run_start", desc=True).limit(50).execute()
    rows = getattr(data, 'data', None)
    if not rows:
        return dbc.Alert("No runs found in run_status table.", color="info")
    df = pd.DataFrame(rows)
    # Format datetime columns for display
    for col in ["run_start", "run_end"]:
        if col in df:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    display_cols = [c for c in ["run_id", "short_description", "run_start", "run_end", "run_status", "scope_of_run", "user_id"] if c in df.columns]
    # Add checkbox column
    table_header = html.Thead(html.Tr([
        html.Th(dcc.Checklist(id="select-all-checkbox", options=[{"label": "", "value": "all"}], value=[], inline=True, style={"margin": "0"}), style={"width": "40px"})
    ] + [html.Th(col) for col in display_cols]))
    table_body = html.Tbody([
        html.Tr([
            html.Td(dcc.Checklist(id={"type": "row-checkbox", "index": int(df.iloc[i]["run_id"])}, options=[{"label": "", "value": int(df.iloc[i]["run_id"])}], value=[], inline=True, style={"margin": "0"})),
            *[html.Td(df.iloc[i][col]) for col in display_cols]
        ], id={"type": "row", "index": int(df.iloc[i]["run_id"])}) for i in range(len(df))
    ])
    table = dbc.Table([table_header, table_body], striped=True, bordered=True, hover=True, responsive=True, className="mt-3")
    # Add action buttons (initially disabled)
    download_btn = dbc.Button("Download Output", id="download-selected-btn", color="success", className="me-2", disabled=True)
    publish_btn = dbc.Button("Publish", id="publish-selected-btn", color="primary", disabled=True)
    feedback_area = html.Div(id="status-table-feedback", className="mt-2")
    return html.Div([
        table,
        html.Div([
            download_btn,
            publish_btn
        ], className="mt-3", id="status-table-action-buttons"),
        feedback_area,
        dcc.Download(id="download-multi-output")
    ])
    # (Exception handling removed; see previous logic)
# --- Callbacks for selection and actions ---
from dash.dependencies import ALL, MATCH

@callback(
    [
        Output("download-selected-btn", "disabled"),
        Output("publish-selected-btn", "disabled"),
    ],
    [
        Input({"type": "row-checkbox", "index": ALL}, "value"),
        Input("run-status-table-container", "children")
    ],
    [State("run-status-table-container", "children")]
)
def update_action_buttons(selected_values, _children, children_state):
    # selected_values: list of lists, each with run_id or empty
    # Find selected run_ids
    selected_run_ids = [v[0] for v in selected_values if v]
    # Always enable the buttons if at least one row is selected
    if not selected_run_ids:
        return True, True
    return False, False


# Combined callback for download and publish actions to avoid duplicate Output error
@callback(
    [
        Output("download-multi-output", "data"),
        Output("run-status-table-container", "children", allow_duplicate=True),
        Output("status-table-feedback", "children")
    ],
    [
        Input("download-selected-btn", "n_clicks"),
        Input("publish-selected-btn", "n_clicks")
    ],
    [State({"type": "row-checkbox", "index": ALL}, "value")],
    prevent_initial_call=True
)
def handle_status_table_actions(download_clicks, publish_clicks, selected_values):
    import os
    import base64
    import datetime
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    selected_run_ids = [v[0] for v in selected_values if v]
    if not selected_run_ids:
        return dash.no_update, dash.no_update, "Please select at least one row."
    if triggered_id == "download-selected-btn":
        files = []
        for run_id in selected_run_ids:
            output_path = f"/workspaces/SolvMate/outputs/{run_id}/Filled_Output_ERGO.xlsx"
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                files.append({
                    "content": encoded,
                    "filename": f"Filled_Output_ERGO_{run_id}.xlsx",
                    "base64": True
                })
        if not files:
            return dash.no_update, dash.no_update, "No output files found for the selected runs."
        if len(files) == 1:
            return dict(content=files[0]["content"], filename=files[0]["filename"], base64=True), dash.no_update, "Download ready."
        return dash.no_update, dash.no_update, "Multiple downloads not yet supported."
    elif triggered_id == "publish-selected-btn":
        if supabase is None:
            return dash.no_update, dash.no_update, "Supabase not configured."
        for run_id in selected_run_ids:
            supabase.table("run_status").update({"run_status": "published", "run_end": datetime.datetime.now().isoformat()}).eq("run_id", run_id).execute()
        # Refresh table by triggering update_run_status_table
        return dash.no_update, update_run_status_table("run-status-table"), "Published selected runs."
    return dash.no_update, dash.no_update, dash.no_update


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
