from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import SecurableType
import os
import io
import base64
import dash

# pages/volumes_upload.py
dash.register_page(
    __name__,
    path='/solvmate/start-calculation',
    title='Start calculation',
    name='Start calculation',
    category='SolvMate',
    icon='material-symbols:calculate'
)

w = WorkspaceClient()

def layout():
    """Return the layout for this view"""
    return dbc.Container([
        # Header section
        html.H1("SolvMate", className="my-4"),
        html.H2("Start calculation", className="mb-3"),
        html.P([
            "This is a PoC for the replacement of the ",
            html.A("SAS Portal", 
                  href="https://stratum.sas94.services.ergo/SASPortal/main.do",
                  target="_blank",
                  className="text-primary")
        ], className="mb-4"),
        
        # Tabs
        dbc.Tabs([
            dbc.Tab(label="Start calculation", tab_id="start-calculation", children=[
                dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Specify a path to an input file of version v30 or later:", 
                                    className="fw-bold mb-2"),
                            dbc.Input(
                                id="file-path-input",
                                type="file",
                                placeholder="Select input file of version v30 or later...",
                                className="mb-3",
                            )
                        ], width=12)
                    ]),
                    dbc.Button(
                        "Start calculation",
                        id="start-calculation-button",
                        color="primary",
                        className="mb-4",
                        size="md"
                    )
                ], className="mt-3"),
                html.Div(id="download-area_RENAME", className="mt-3"),
                html.Div(id="status-area-download_RENAME", className="mt-3")
            ], className="p-3"),
            
            dbc.Tab(label="Status overview", tab_id="code-snippet", children=[
                dcc.Markdown('''```python

...

```''',className="border rounded p-3")
            ], className="p-3"),
            
            
        ], id="tabs", active_tab="start-calculation", className="mb-4")
    ], fluid=True, className="py-4")

@callback(
    [Output("download-area_RENAME", "children"),
     Output("status-area-download_RENAME", "children")],
    Input("start-calculation-button", "n_clicks"),
    State("file-path-input", "value"),
    prevent_initial_call=True
)
def handle_file_download(n_clicks, file_path):
    if not file_path:
        return None, dbc.Alert("Please specify a file path.", color="warning")
    
    try:
        resp = w.files.download(file_path)
        file_data = resp.contents.read()
        file_name = os.path.basename(file_path)
        
        # Encode file data for download
        encoded = base64.b64encode(file_data).decode()
        
        download_link = html.A(
            dbc.Button(
                "Start calculation",
                color="success",
                className="mt-3"
            ),
            href=f"data:application/octet-stream;base64,{encoded}",
            download=file_name
        )
        
        return download_link, dbc.Alert(f"File '{file_name}' is ready for download", 
                                      color="success")
    except Exception as e:
        return None, dbc.Alert(f"Error downloading file: {str(e)}", color="danger")

# Make layout available at module level
__all__ = ['layout']
