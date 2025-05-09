from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash


dash.register_page(
    __name__,
    path="/Database/output_mapping_test",
    title='Output mapping',
    name='Output mapping',
    category='Database configuration'
)


def layout():
    """Return the layout for this view"""
    return dbc.Container([
        # Haupttitel
        html.H1("Titel der Seite", className="my-4 text-center"),
        # Untertitel
        html.H2("Untertitel der Seite", className="mb-3 text-center"),
        # Beschreibung
        html.P("Hier ist eine Beschreibung der Seite, die über die gesamte Breite geht.", className="text-center mb-4"),

        # Aufteilung in zwei Spalten
        dbc.Row([
            dbc.Col([
                html.H3("Linker Block"),
                html.P("Hier ist eine Beschreibung für den linken Block."),
                dbc.Button("Download", id="download-button", color="primary", className="mt-2"),
            ], width=6, className="border p-3"),

            dbc.Col([
                html.H3("Rechter Block"),
                html.P("Hier ist eine Beschreibung für den rechten Block."),
                dcc.Upload(
                    id='upload-data',
                    children=html.Button('Upload Datei'),
                    multiple=False
                ),
                dbc.Button("Upload Bestätigen", id="upload-button", color="success", className="mt-2"),
                html.Div(id='upload-output', className='mt-3'),
            ], width=6, className="border p-3"),
        ])
    ], fluid=True, className="py-4")

@callback(
    Output("upload-output", "children"),
    Input("upload-button", "n_clicks"),
    Input("upload-data", "filename"),
    prevent_initial_call=True
)
def handle_upload(n_clicks, filename):
    if filename:
        return f"Die Datei '{filename}' wurde erfolgreich hochgeladen!"
    return "Bitte lade eine Datei hoch."

# Make layout available at module level
__all__ = ['layout']