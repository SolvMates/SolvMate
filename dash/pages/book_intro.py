from dash import html, dcc
import dash_bootstrap_components as dbc
import dash

# pages/book_intro.py
dash.register_page(__name__, path="/", title="Introduction", name="Introduction")


def create_group_cards():
    # Define category metadata with consistent order and grouping
    category_metadata = {
        "End-to-End": ["Description", "Run test"],
        "Database configuration": ["Output mapping"],
    }

    cards = []
    # Create cards in specified order
    for category, views in category_metadata.items():
        category_pages = [
            page
            for page in dash.page_registry.values()
            if page.get("category") == category
        ]

        if category_pages:  # Only create card if there are pages in this category
            # Sort pages according to the specified view order
            ordered_pages = sorted(
                category_pages,
                key=lambda x: views.index(x["name"])
                if x["name"] in views
                else len(views),
            )

            cards.append(
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            category,
                                            className="h5 mb-3",
                                        ),
                                        html.Ul(
                                            [
                                                html.Li(
                                                    dcc.Link(
                                                        page["name"],
                                                        href=page["relative_path"],
                                                        className="recipe-link",
                                                        style={
                                                            "display": "block",
                                                            "padding": "8px 12px",
                                                            "borderRadius": "4px",
                                                            "color": "#1b3139",
                                                            "textDecoration": "none",
                                                        },
                                                    )
                                                )
                                                for page in ordered_pages
                                            ],
                                            className="list-unstyled mb-0",
                                        ),
                                    ]
                                )
                            ],
                            className="h-100 bg-light",
                        )
                    ],
                    md=6,
                    lg=3,
                    className="mb-4",
                )
            )

    return dbc.Row(cards, className="g-4")


def layout():
    return dbc.Container(
        [
            html.Div(
                [
                    html.H1(
                        ["SolvMate - Testing Dashboard"], className="display-3 mb-4"
                    ),
                    html.Div(
                        [
                            html.P(
                                "Welcome to SolvMate! This platform helps you test, validate, and manage your data workflows for regulatory and business reporting. SolvMate streamlines the process of running end-to-end calculations, mapping outputs, and configuring database connections—all in one place.",
                                className="lead mt-3 mb-2",
                            ),
                        ],
                        className="d-flex align-items-center mb-3",
                    ),
                    html.P(
                        [
                            html.B("Scripts Tab: "),
                            "Access the main testing and configuration scripts here. The End-to-End group lets you run full workflow tests and view descriptions. The Database configuration group allows you to map outputs and manage database-related settings.",
                        ],
                        className="mb-2",
                    ),
                    html.P(
                        [
                            html.B("Links Tab: "),
                            "Find helpful resources and documentation relevant to SolvMate and its ecosystem.",
                        ],
                        className="mb-4",
                    ),
                ],
                className="py-3",
            ),
            html.H3("Scripts", className="mb-4 pb-2 border-bottom"),
            create_group_cards(),
        ],
        fluid=True,
        className="py-4",
    )


# Make layout available at module level
__all__ = ["layout"]
