from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import requests
import pandas as pd
from databricks.sdk.core import Config
from dash.exceptions import PreventUpdate
import dash


cfg = Config()

def layout():
    return dbc.Container([
        html.H1("Genie", className="my-4"),
        html.H2("Converse with your data", className="mb-3"),
        html.P([
            "This app uses ",
            html.A(
                "Databricks AI/BI Genie",
                href="https://www.databricks.com/product/ai-bi",
                target="_blank"
            ),
            " to let users ask questions about your data for instant insights."
        ], className="mb-4"),
        
        dbc.Tabs([
            # Try it tab
            dbc.Tab(label="Try it", children=[
                dbc.Form([
                    dbc.Label("Genie Space ID:", className="mt-3"),
                    dbc.Input(
                        id="genie-space-input",
                        type="text",
                        placeholder="Enter your Genie Space ID",
                        style={
                            "backgroundColor": "#f8f9fa",
                            "border": "1px solid #dee2e6",
                            "boxShadow": "inset 0 1px 2px rgba(0,0,0,0.075)"
                        }
                    ),
                    
                    dbc.Label("Authentication Token:", className="mt-3"),
                    dbc.Input(
                        id="auth-token-input",
                        type="password",
                        placeholder="Enter your authentication token",
                        style={
                            "backgroundColor": "#f8f9fa",
                            "border": "1px solid #dee2e6",
                            "boxShadow": "inset 0 1px 2px rgba(0,0,0,0.075)"
                        }
                    ),
                    
                    dbc.Label("Your question:", className="mt-3"),
                    dbc.InputGroup([
                        dbc.Input(
                            id="question-input",
                            type="text",
                            placeholder="Ask Genie a question",
                            style={
                                "backgroundColor": "#f8f9fa",
                                "border": "1px solid #dee2e6",
                                "boxShadow": "inset 0 1px 2px rgba(0,0,0,0.075)"
                            }
                        ),
                        dbc.Button(
                            "Ask",
                            id="ask-button",
                            color="primary"
                        )
                    ])
                ], className="mb-4"),
                
                # Chat history area
                html.Div(id="chat-history-genie", className="mt-4"),
                
                # Status/error messages
                html.Div(id="status-area-genie", className="mt-3")
            ], className="p-3"),
            
            # Code snippet tab
            dbc.Tab(label="Code snippet", children=[
                dcc.Markdown('''```python
import requests
from databricks.sdk.core import Config

# Configuration
cfg = Config()
genie_space_id = "your_space_id"
authentication_token = "your_auth_token"

headers = {
    'Authorization': f'Bearer {authentication_token}'
}

def start_conversation(genie_space_id, question):
    url = f'{cfg.host}/api/2.0/genie/spaces/{genie_space_id}/start-conversation'
    response = requests.post(url, json={'content': question}, headers=headers)
    return response.json()

# Start conversation
response = start_conversation(genie_space_id, "What is the total revenue by region?")
```''', className="p-4 border rounded")
            ], className="p-3"),
            
            # Requirements tab
            dbc.Tab(label="Requirements", children=[
                dbc.Row([
                    dbc.Col([
                        html.H4("Permissions", className="mb-3"),
                        html.Ul([
                            html.Li("Genie space"),
                            html.Li("API access token")
                        ], className="mb-4")
                    ]),
                    dbc.Col([
                        html.H4("Databricks resources", className="mb-3"),
                        html.Ul([
                            html.Li("AI/BI Genie Conversations API")
                        ], className="mb-4")
                    ]),
                    dbc.Col([
                        html.H4("Dependencies", className="mb-3"),
                        html.Ul([
                            html.Li(["Requests - ", html.Code("requests")]),
                            html.Li(["Databricks SDK - ", html.Code("databricks-sdk")]),
                            html.Li(["Pandas - ", html.Code("pandas")]),
                            html.Li(["Dash - ", html.Code("dash")])
                        ], className="mb-4")
                    ])
                ])
            ], className="p-3")
        ], className="mb-4")
    ], fluid=True, className="py-4")

@callback(
    [Output("chat-history-genie", "children"),
     Output("status-area-genie", "children")],
    Input("ask-button", "n_clicks"),
    [State("genie-space-input", "value"),
     State("auth-token-input", "value"),
     State("question-input", "value")],
    prevent_initial_call=True
)
def update_chat(n_clicks, space_id, token, question):
    if not all([space_id, token, question]):
        return no_update, dbc.Alert(
            "Please fill in all fields",
            color="warning"
        )
    
    try:
        # API interaction code would go here
        # For now, just return a placeholder response
        return [
            html.Div([
                dbc.Card(
                    dbc.CardBody([
                        html.P(f"Q: {question}"),
                        html.P("A: Processing your question...")
                    ])
                )
            ], className="mb-3")
        ], None
    except Exception as e:
        return no_update, dbc.Alert(
            f"An error occurred: {str(e)}",
            color="danger"
        )

# Make layout available at module level
__all__ = ['layout']