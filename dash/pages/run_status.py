from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash

# pages/run_status.py
dash.register_page(
    __name__,
    path="/End-to-End/Run-Status-Table",
    title='Run Status Table',
    name='Run Status Table',
    category='End-to-End'
)

def layout():
    """Return the layout for the Run Status Table view"""
    return dbc.Container([
        html.H1("Run Status Table", className="my-4"),
        html.Div(id="run-status-table-container", className="p-3")
    ], fluid=True, className="py-4")

# --- Run Status Table Callback ---
import pandas as pd



@callback(
    Output("run-status-table-container", "children"),
    Input("run-status-table-container", "id")
)
def update_run_status_table(_):
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
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import base64
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
from supabase import create_client, Client
supabase = None
if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)

from dash.dependencies import Output, Input, State, ALL
import random

# Removed perform calculation callback

# Make layout available at module level
__all__ = ['layout']
