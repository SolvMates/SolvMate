from dash import Dash, html, dcc, page_container
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import dash
from collections import defaultdict

app = Dash(__name__, 
           use_pages=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)

app.title = "SolvMate - Testing App"

def create_sidebar():
    nav_items = []
    
    # Add Introduction link with icon
    nav_items.append(
        dbc.NavLink([
            DashIconify(icon="material-symbols:menu-book", className="me-2"),
            "Introduction"
        ],
        href="/",
        className="sidebar-link text-dark fw-bold",
        active="exact"
        )
    )
    
    # Define category and page order
    sidebar_structure = {
        'End-to-End': [
            'End-to-End test'
        ],
        'Market Risk': [
            'Market (w/o ConcR & Curr)',
            'CurrR',
            'ConcR'
        ],
        'Counterparty Default': [
            'Type 1',
            'Type 2',
            'Counterparty Hyp'
        ]
    }
    
    # Group pages by category
    categories = defaultdict(list)
    for page in dash.page_registry.values():
        if page.get("category"):
            categories[page["category"]].append(page)
    
    # Create navigation items in specified order
    for category, page_order in sidebar_structure.items():
        if category in categories:
            category_pages = categories[category]
            # Sort pages according to the specified order
            ordered_pages = sorted(
                category_pages,
                key=lambda x: page_order.index(x["name"]) if x["name"] in page_order else len(page_order)
            )
            
            nav_items.append(
                html.Div([
                    # Category header without icon
                    html.Div(category, className="h6 mt-3 mb-2"),
                    # Pages under the category
                    dbc.Nav([
                        dbc.NavLink([
                            page["name"]
                        ],
                        href=page["relative_path"],
                        active="exact",
                        className="sidebar-link text-dark ps-3"
                        ) for page in ordered_pages
                    ], vertical=True)
                ])
            )
    
    return html.Div(nav_items, className="py-2")

app.layout = html.Div([
    dbc.Container([
        dcc.Location(id='url', refresh=False),
        dbc.Row([
            # Sidebar
            dbc.Col([
                html.Div([
                    html.Img(src="assets/logo.svg", className="logo ms-4", style={
                        'width': '30px',
                        'margin-top': '20px'
                    }),
                ], className="sidebar-header"),
                html.Div(create_sidebar(), className="ps-4")
            ], width=2, className="bg-light border-end overflow-auto p-0"),
            
            dbc.Col([
                page_container
            ], width=10, className="content p-0 px-4 py-4")
        ], className="g-0")
    ], fluid=True, className="vh-100 p-0")
])

if __name__ == '__main__':
    app.run_server(debug=True)
