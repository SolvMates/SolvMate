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
                    dbc.Spinner(html.Div(id="download-area_e2e"), size="md", color="primary", fullscreen=False),
                    dcc.Textarea(
                        id="log-box",
                        className="mt-3",
                        style={'width': '100%', 'height': '200px', 'fontFamily': 'monospace'},
                        readOnly=True,
                        placeholder="Execution logs will appear here..."
                    ),
                    dcc.Interval(
                        id='log-update-interval',
                        interval=500,  # update every 500ms
                        n_intervals=0,
                        disabled=True
                    )
                ], className="mt-3"),
                html.Div(id="status-area_e2e", className="mt-3")
        ], fluid=True, className="py-4")

# --- Backend logic ---
import base64
import tempfile
import importlib
from dash import ctx
import sys
import threading
import queue
import io

# Global variables for log handling
log_queue = queue.Queue()
current_run_status = {'running': False}

# Custom stdout redirector
class StreamToQueue(io.StringIO):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def write(self, text):
        if text.strip():  # Only queue non-empty lines
            self.queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] {text.strip()}")

    def flush(self):
        pass
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
        Output("selected-filename", "children"),
        Output("log-box", "value"),
        Output("log-update-interval", "disabled")
    ],
    [
        Input("start-calculation-button", "n_clicks"),
        Input("file-path-input", "filename"),
        Input("log-update-interval", "n_intervals")
    ],
    [
        State("file-path-input", "contents"),
        State("file-path-input", "filename"),
        State("description-input", "value"),
        State("scope-input", "value"),
        State("log-box", "value")
    ],
    prevent_initial_call=True
)
def handle_calculation(n_clicks, uploaded_filename, n_intervals, file_contents, file_name, description, scope, current_log):
    ctx_triggered = ctx.triggered_id if hasattr(ctx, 'triggered_id') else None
    filename_display = f"Selected file: {uploaded_filename}" if uploaded_filename else "No file selected."
    
    # Handle file selection
    if ctx_triggered == "file-path-input":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, filename_display, dash.no_update, dash.no_update
    
    # Handle interval updates
    if ctx_triggered == "log-update-interval":
        if not current_run_status['running']:
            # If calculation is not running, collect all remaining logs
            logs = []
            while not log_queue.empty():
                logs.append(log_queue.get())
            
            if logs:  # If we have final logs to show
                log_text = current_log + "\n" + "\n".join(logs) if current_log else "\n".join(logs)
                if "Error during run" in log_text:
                    return (
                        dbc.Alert("Calculation failed. See logs for details.", color="danger"),
                        False,  # enable button
                        "Start calculation",
                        None,
                        dash.no_update,
                        log_text,
                        True  # disable interval
                    )
                else:
                    return (
                        dbc.Alert("Calculation completed successfully!", color="success"),
                        False,  # enable button
                        "Start calculation",
                        None,
                        dash.no_update,
                        log_text,
                        True  # disable interval
                    )
            
            return dash.no_update, False, "Start calculation", dash.no_update, dash.no_update, dash.no_update, True
        
        # If calculation is still running, show current logs
        logs = []
        while not log_queue.empty():
            logs.append(log_queue.get())
        
        if logs:
            log_text = current_log + "\n" + "\n".join(logs) if current_log else "\n".join(logs)
            return dash.no_update, True, "Running...", dash.no_update, dash.no_update, log_text, False
        
        return dash.no_update, True, "Running...", dash.no_update, dash.no_update, dash.no_update, False
    
    # Handle start button click
    if not file_contents or not file_name:
        return dbc.Alert("Please select an input file.", color="warning"), False, "Start calculation", None, filename_display, "", True
    if not description or not description.strip():
        return dbc.Alert("Please enter a description before running.", color="warning"), False, "Start calculation", None, filename_display, "", True
    
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
    # Set running status and clear previous logs
    current_run_status['running'] = True
    while not log_queue.empty():
        log_queue.get()
    
    def run_calculation_thread():
        # Save the original stdout
        old_stdout = sys.stdout
        try:
            # Redirect stdout to our custom handler
            sys.stdout = StreamToQueue(log_queue)
            
            print("Starting calculation...")
            print(f"Run ID: {run_id}")
            print(f"Processing file: {file_name}")
            
            # Import and run the calculation
            solvmate_main = importlib.import_module("src.solvmate_main")
            solvmate_main.run_calculation(temp_input_path, run_id)
            
            print("Calculation completed successfully")
            
        except Exception as e:
            print(f"Error during run: {str(e)}")
            raise e
        finally:
            # Always restore the original stdout and mark as not running
            sys.stdout = old_stdout
            current_run_status['running'] = False

    # Start calculation in a separate thread
    calculation_thread = threading.Thread(target=run_calculation_thread)
    calculation_thread.start()
    
    # Return immediately to disable the button
    # Return immediately to disable the button and enable the interval
    return (
        dbc.Alert("Calculation started...", color="info"),
        True,  # disable button
        "Running...",
        None,
        filename_display,
        "Starting calculation...",
        False  # enable interval
    )# Make layout available at module level
__all__ = ['layout']
