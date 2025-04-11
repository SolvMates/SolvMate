from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash

# pages/E2E_run_test.py
dash.register_page(
    __name__,
    path="/CPD/cpd-hyp-test",
    title='Counterparty Hyp',
    name='Counterparty Hyp',
    category='Counterparty Default'
)

def layout():
    """Return the layout for this view"""
    return dbc.Container([
        # Header section
        html.H1("Counterparty Hyp", className="my-4"),
        html.H2("Perform calculation", className="mb-3"),
        
        
        # Tabs
        dbc.Tabs([
            # First tab: Perform calculation
            dbc.Tab(label="Perform calculation", tab_id="perform-calculation", children=[
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
                html.Div(id="status-area_cpd_hyp", className="mt-3")
            ], className="p-3"),
            
            # Second tab: Log
            dbc.Tab(label="Log", tab_id="log", children=[
                dcc.Markdown(
                    '''
                    ```
                    Here we would see the log including any potential error messages of the run...
                    ```
                    ''',
                    className="border rounded p-3"
                )
            ], className="p-3"),
            
        ], id="tabs", active_tab="perform-calculation", className="mb-4")
    ], fluid=True, className="py-4")

@callback(
    Output("status-area_cpd_hyp", "children"),
    Input("start-calculation-button", "n_clicks"),
    prevent_initial_call=True
)
def handle_start_calculation(n_clicks):
    return dbc.Alert(
        "No functionality here, yet, but this button would run the whole calculation logic, that is completed at that time.",
        color="info"
    )

# Make layout available at module level
__all__ = ['layout']
