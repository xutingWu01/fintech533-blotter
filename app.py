from dash import Dash, html, dcc, dash_table, Input, Output, State
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
from datetime import date
import base64
import dash_bootstrap_components as dbc
import helper
import percepto


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
                dbc.Label("Please enter start date and end date for the data which you want to query"),
                dcc.DatePickerRange(
                    id='my-date-picker-range',
                    min_date_allowed=datetime(2020, 3, 1),
                    max_date_allowed=datetime.now(),
                ),
                html.Br(),
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

raw_data_table = dbc.Card(
    dbc.CardBody(
        [
            html.H2('RAW DATA', className="card-title"),
            dash_table.DataTable(
                    id="raw-data",
                    page_action='none',
                    style_table={'height': '225px', 'overflowY': 'auto'}
                ),
        ]
    )
)

predict_data_table = dbc.Card(
    dbc.CardBody(
        [
            html.H3('Prediction'),
            dash_table.DataTable(
                    id="predict-data",
                    page_action='none',
                    style_table={'height': '100px', 'overflowY': 'auto'},
                    style_cell_conditional=[
                            {'if': {'column_id': 'Date'},
                             'width': '10%'},
                            {'if': {'column_id': 'Success'},
                             'width': '10%'},
                        ]
                ),
        ]
    )
)

actual_data_table = dbc.Card(
    dbc.CardBody(
        [
            html.H3('Actual Data'),
            dash_table.DataTable(
                    id="actual-data",
                    page_action='none',
                    style_table={'height': '100px', 'overflowY': 'auto'},
                    style_cell_conditional=[
                        {'if': {'column_id': 'Date'},
                         'width': '30%'},
                        {'if': {'column_id': 'Success'},
                         'width': '30%'},
                    ]
                ),
        ]
    )
)


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

predict_btn = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Enter the date you would like to predict"),
                dcc.DatePickerSingle(
                    id='predict-date',
                    month_format='M-D-Y-Q',
                    placeholder='M-D-Y-Q',
                    date=date(2021, 5, 8)
                ),
                html.Hr(),
                dbc.Button('Start Prediction', color="primary", id='predict', n_clicks=0, className="mb-3", ),
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
        style_table={'height': '230px', 'overflowY': 'auto'}
    ),
])

exit_table = html.Div([
    html.H2('EXIT-BLOTTER'),
    dash_table.DataTable(
        id="exit-blotter-tbl",
        page_action='none',
        style_table={'height': '230px', 'overflowY': 'auto'}
    ),
])

tabs = dbc.Card(
    dbc.CardBody(
        [
            html.H2("Blotter"),
            dbc.Tabs(
                    [
                        dbc.Tab(label="Blotter", tab_id="Blotter"),
                        dbc.Tab(label="Ledger", tab_id="Ledger"),
                    ],
                    id="tabs",
                    active_tab="Blotter",
                ),
            html.Div(id="tab-content", className="p-4"),
        ]
    )
)

image_filename = 'fig.png'
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

app.layout = dbc.Container(
    [
        dcc.Store(id="entry"),
        dcc.Store(id="ledger"),
        # Top Banner
        html.Div(
            className="study-browser-banner row",
            children=[
                html.H2(className="h2-title", children="Plot Analysis-[Xuting Wu(xw218), Aohua Zhang(az147)]"),
                html.H2(className="h2-title-mobile", children="Plot Analysis-[Xuting Wu(xw218), Aohua Zhang(az147)]"),
            ],
        ),
        # Body of the App
        html.Div(
            className="row app-body",
            children=[
                #user controls
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(controls, md=4),
                        dbc.Col(raw_data_table, md=8),
                    ],
                    align="center",
                ),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(paramater_table, md=4),
                        dbc.Col(tabs, md=8),
                    ],
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(predict_btn, md=4),
                        dbc.Col(predict_data_table, md=4),
                        dbc.Col(actual_data_table, md=4)
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
    Output('asset-id', 'value'),
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
    return ivv_prc.to_dict('records'), None, False, asset_id



# generate blotter
@app.callback(
    Output("entry", "data"), Output("ledger", "data"),
    Input("submit", "n_clicks"),
    [State("alpha", "value"), State("n", "value"), State("alpha2", "value"), State("n2", "value"), State("asset-id", "value")],
    prevent_initial_call=True
)
def render_blotter(n_clicks, alpha1, n1, alpha2, n2, asset_id):
    print("rendering result")
    entry = helper.generateOrders(float(alpha1), int(n1), float(alpha2), int(n2), ivv_prc, asset_id)
    ledger = helper.generateLedger(entry)
    return entry.to_dict('records'), ledger.to_dict('records')


@app.callback(
    Output("predict-data", "data"), Output("actual-data", "data"),
    Input("predict", "n_clicks"),
    State("predict-date", "date"),
    prevent_initial_call=True
)
def render_predict(n_clicks, predict_date):
    print("predict-result for" + predict_date)
    predict, actual = percepto.percep(predict_date)
    print(("-----------------"))
    print(predict)
    print(("-----------------"))
    print(actual)
    # start process data
    return predict.to_dict('records'), actual.to_dict('records')

@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "active_tab"), Input("entry", "data"), Input("ledger", "data")],
)
def render_tab_content(active_tab, entry, ledger):
    """
    This callback takes the 'active_tab' property as input, as well as the
    stored graphs, and renders the tab content depending on what the value of
    'active_tab' is.
    """
    if active_tab and entry and exit is not None:
        if active_tab == "Blotter":
            return html.Div([
                # html.H2('ENTRY-BLOTTER'),
                dash_table.DataTable(
                    data = entry,
                    id="entry-blotter-tbl",
                    page_action='none',
                    style_table={'height': '230px', 'overflowY': 'auto'}
                ),
            ])
        elif active_tab == "Ledger":
            return html.Div([
                dash_table.DataTable(
                    data = ledger,
                    id="ledger-tbl",
                    page_action='none',
                    style_table={'height': '230px', 'overflowY': 'auto'}
                ),
            ])
    return "No tab selected"

if __name__ == '__main__':
    app.run_server(debug=True)
    # serve(app)