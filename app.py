from dash import Dash, html, dcc, dash_table, Input, Output, State
from datetime import datetime
import plotly.express as px
import os
import base64
import dash_bootstrap_components as dbc
import helper


# app = Dash(__name__)
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
# takes python and generate html
controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Asset"),
                dbc.Input(id='asset-id', type='text', value="IVV"),
                html.Br(),
            ]
        ),
        # date picker
        html.Div(
            [
                html.H5("Please enter start date and end date for the data which you want to query"),
                dcc.DatePickerRange(
                    id='my-date-picker-range',
                    min_date_allowed=datetime(2021, 11, 1),
                    max_date_allowed=datetime.now(),
                ),
                # html.Br(),
                dbc.Alert(id='query_date_div', is_open=False,),
            ]
        ),
        html.Div(
            [
                html.Hr(),
                dbc.Row(dbc.Button('Query', color="primary", id='query', n_clicks=0, className="mb-3",)),
            ]
        )
    ],
    body=True,
)

raw_data_table = html.Div([
    html.H2('RAW DATA'),
    dash_table.DataTable(
            id="raw-data",
            page_action='none',
            style_table={'height': '300px', 'overflowY': 'auto'}
        ),
])

paramater_table = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("alpha1"),
                dbc.Input(id='alpha', type='number', value="-0.01"),
            ]
        ),
        html.Div(
            [
                dbc.Label("n1"),
                dbc.Input(id='n', type='number', value="3"),
            ]
        ),
        html.Div(
            [
                dbc.Label("alpha2"),
                dbc.Input(id='alpha2', type='number', value="0.01"),
            ]
        ),
        html.Div(
            [
                dbc.Label("n2"),
                dbc.Input(id='n2', type='number', value="5"),
            ]
        ),
        html.Div(
            [
                html.Hr(),
                dbc.Row(dbc.Button('Submit', color="primary", id='submit', n_clicks=0, className="mb-3",)),
            ]
        )
    ],
    body=True,
)

entry_table = html.Div([
    html.H2('ENTRY-BLOTTER'),
    dash_table.DataTable(
        id="entry-blotter-tbl",
        page_action='none',
        style_table={'height': '300px', 'overflowY': 'auto'}
    ),
])

exit_table = html.Div([
    html.H2('EXIT-BLOTTER'),
    dash_table.DataTable(
        id="exit-blotter-tbl",
        page_action='none',
        style_table={'height': '300px', 'overflowY': 'auto'}
    ),
])

tabs = html.Div([
    html.H2("Blotter"),
    dbc.Tabs(
            [
                dbc.Tab(label="Entry", tab_id="Entry"),
                dbc.Tab(label="Exit", tab_id="Exit"),
            ],
            id="tabs",
            active_tab="Entry",
        ),
    html.Div(id="tab-content", className="p-4"),
])

image_filename = 'fig.png'
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

app.layout = dbc.Container(
    [
        dcc.Store(id="entry"),
        dcc.Store(id="exit"),
    html.Div([
        html.H1("Blotter for entry and exit blotter"),
        html.H5("[Xuting Wu(xw218), Aohua Zhang(az147)]"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(controls, md=4),
                dbc.Col(raw_data_table, md=8),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(paramater_table, md=4),
                dbc.Col(tabs, md=8),
            ],
            align="center",
        ),
        # dbc.Row(entry_table, md=8),
        # dbc.Row(exit_table, md=12),
    ]),
    html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'height':'50%', 'width':'50%'}),
    ],
    fluid=True,
)

# Whenever an input property changes, the function that the callback decorator wraps will get called automatically
# query data from refinitiv
@app.callback(
    Output("raw-data", "data"),
    Output("query_date_div", "children"),
    Output("query_date_div", "is_open"),
    Input("query", "n_clicks"),
    [State('asset-id', 'value'), State('my-date-picker-range', 'start_date'),
     State('my-date-picker-range', 'end_date'), State("query_date_div", "is_open")],
    prevent_initial_call=True
)
def query_refinitiv(n_clicks, asset_id, start_date, end_date, is_open):
    if start_date is None or end_date is None:
        return [], "Please enter start and end date", True
    # get start dates and end dates
    start_date_object = datetime.fromisoformat(start_date)
    start_date_string = start_date_object.strftime("%Y-%m-%d")
    end_date_object = datetime.fromisoformat(end_date)
    end_date_string = end_date_object.strftime("%Y-%m-%d")

    global ivv_prc
    ivv_prc = helper.query_date(start_date_string, end_date_string, asset_id)
    return ivv_prc.to_dict('records'), None, False



# generate blotter
@app.callback(
    Output("entry", "data"),
    Output("exit", "data"),
    Input("submit", "n_clicks"),
    [State("alpha", "value"), State("n", "value"), State("alpha2", "value"), State("n2", "value")],
    prevent_initial_call=True
)
def render_blotter(n_clicks, alpha1, n1, alpha2, n2):
    print("rendering result")
    entry_orders, exit_orders = helper.generateOrders(float(alpha1), int(n1), float(alpha2), int(n2), ivv_prc)
    return entry_orders.to_dict('records'), exit_orders.to_dict('records')


@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "active_tab"), Input("entry", "data"), Input("exit", "data")],
)
def render_tab_content(active_tab, entry, exit):
    """
    This callback takes the 'active_tab' property as input, as well as the
    stored graphs, and renders the tab content depending on what the value of
    'active_tab' is.
    """
    if active_tab and entry and exit is not None:
        if active_tab == "Entry":
            return html.Div([
                html.H2('ENTRY-BLOTTER'),
                dash_table.DataTable(
                    data = entry,
                    id="entry-blotter-tbl",
                    page_action='none',
                    style_table={'height': '300px', 'overflowY': 'auto'}
                ),
            ])
        elif active_tab == "Exit":
            return html.Div([
                html.H2('EXIT-BLOTTER'),
                dash_table.DataTable(
                    data = exit,
                    id="exit-blotter-tbl",
                    page_action='none',
                    style_table={'height': '300px', 'overflowY': 'auto'}
                ),
            ])
    return "No tab selected"

if __name__ == '__main__':
    app.run_server(debug=True)
    # serve(app)