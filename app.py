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
import numpy as np

# app = Dash(__name__)
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
# takes python and generate html
controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Asset"),
                dbc.Input(id='asset-id', type='text', value="AAPL.O"),
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
                    start_date=datetime(2020, 3, 1),
                    end_date = datetime(2023, 3, 1),
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
#
# predict_data_table = dbc.Card(
#     dbc.CardBody(
#         [
#             html.H3('Prediction'),
#             dash_table.DataTable(
#                     id="predict-data",
#                     page_action='none',
#                     style_table={'height': '100px', 'overflowY': 'auto'},
#                     style_cell_conditional=[
#                             {'if': {'column_id': 'Date'},
#                              'width': '10%'},
#                             {'if': {'column_id': 'Success'},
#                              'width': '10%'},
#                         ]
#                 ),
#         ]
#     )
# )
#
# actual_data_table = dbc.Card(
#     dbc.CardBody(
#         [
#             html.H3('Actual Data'),
#             dash_table.DataTable(
#                     id="actual-data",
#                     page_action='none',
#                     style_table={'height': '100px', 'overflowY': 'auto'},
#                     style_cell_conditional=[
#                         {'if': {'column_id': 'Date'},
#                          'width': '30%'},
#                         {'if': {'column_id': 'Success'},
#                          'width': '30%'},
#                     ]
#                 ),
#         ]
#     )
# )


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
                dbc.Label("n3"),
                dbc.Input(id='n3', type='number', value="50"),
            ]
        ),

        html.Div(
            [
                html.Hr(),
                dbc.Row(dbc.Button('Submit', color="primary", id='submit', n_clicks=0, className="mb-3",)),
                dbc.Row(dbc.Button('Start Prediction', color="primary", id='predict', n_clicks=0, className="mb-3", )),
            ]
        )
    ],
    body=True,
)

# predict_btn = dbc.Card(
#     [
#         html.Div(
#             [
#                 dbc.Label("Enter the date you would like to predict"),
#                 dcc.DatePickerSingle(
#                     id='predict-date',
#                     month_format='M-D-Y-Q',
#                     placeholder='M-D-Y-Q',
#                     date=date(2021, 5, 8)
#                 ),
#                 html.Hr(),
#                 dbc.Button('Start Prediction', color="primary", id='predict', n_clicks=0, className="mb-3", ),
#             ]
#         )
#     ],
#     body=True,
# )

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
                        dbc.Tab(label="Ledger2", tab_id="Ledger2"),
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
        dcc.Store(id="ledger2"),
        # Top Banner
        html.Div(
            className="study-browser-banner row",
            children=[
                html.H2(className="h2-title", children="Trading Analysis-[Xuting Wu(xw218), Aohua Zhang(az147)]"),
                html.H2(className="h2-title-mobile", children="Trading Analysis-[Xuting Wu(xw218), Aohua Zhang(az147)]"),
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
                        dcc.Graph(id="ab-plot"),
                        dcc.RangeSlider(
                                id='ab-range-slider',
                                min = 0,
                                max = 25,
                                marks = None,
                                step = 1
                        ),
                        dcc.Graph(id="dumb-plot"),
                        dcc.RangeSlider(
                            id='dumb-range-slider',
                            min=0,
                            max=25,
                            marks=None,
                            step=1
                        )
                        # dbc.Col(predict_data_table, md=4),
                        # dbc.Col(actual_data_table, md=4)
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
    global start_date_string
    global end_date_string
    start_date_object = datetime.fromisoformat(start_date)
    start_date_string = start_date_object.strftime("%Y-%m-%d")
    end_date_object = datetime.fromisoformat(end_date)
    end_date_string = end_date_object.strftime("%Y-%m-%d")

    global ivv_prc
    ivv_prc = helper.query_date(start_date_string, end_date_string, asset_id)
    return ivv_prc.to_dict('records'), None, False, asset_id



# generate blotter
@app.callback(
    Output("entry", "data"), Output("ledger", "data"), Output("ledger2", "data"),
    Input("submit", "n_clicks"),
    [State("alpha", "value"), State("n", "value"), State("alpha2", "value"), State("n2", "value"), State("n3", "value"), State("asset-id", "value")],
    prevent_initial_call=True
)
def render_blotter(n_clicks, alpha1, n1, alpha2, n2, n3, asset_id):
    print("rendering result")
    global entry
    global ledger
    global ledger2
    entry = helper.generateOrders(float(alpha1), int(n1), float(alpha2), int(n2), ivv_prc, asset_id)
    ledger = helper.generateLedger(entry)
    ledger2 = percepto.whole_percep(int(n3))
    # ledger2.drop('Unnamed', axis=1, inplace=True)
    innerJoinRtn(ledger2)
    return entry.to_dict('records'), ledger.to_dict('records'), ledger2.to_dict('records')

def innerJoinRtn(ledger2):
    # generate IVV rtn for smart ledger
    print("try inner join")
    global ivv_benchmark
    global filtered_ledger2
    ivv_benchmark = pd.DataFrame(columns=['dt_enter', 'dt_exit', 'rtn_benchmark'])
    filtered_ledger2 = pd.DataFrame(columns=['dt_enter', 'dt_exit', 'rtn'])
    ivv = helper.query_date(start_date_string, end_date_string, 'IVV')
    for index, row in ledger2.iterrows():
        enter_date = row['dt_enter']
        exit_date = row['dt_exit']
        rtn_str = ""
        if type(exit_date) is str and row['predict_success'] == '1.0':
            enter_price_row = ivv.loc[ivv['Date']==datetime.strptime(enter_date, '%Y-%m-%d').date()]
            enter_price = enter_price_row.iloc[0]['Close Price']
            # print(enter_price)
            exit_price_row = ivv.loc[ivv['Date']==datetime.strptime(exit_date, '%Y-%m-%d').date()]
            exit_price = exit_price_row.iloc[0]['Close Price']
            n = helper.count_bdays(enter_date, exit_date)
            if(n==0):
                print("n is 0")
            else:
                rtn = np.log(float(exit_price) / float(enter_price)) / int(n)
                rtn_str = '{:.3%}'.format(rtn)
        # ledger2.at[index, 'rtn'] = rtn_str
            data = {"dt_enter": row['dt_enter'], "dt_exit": row['dt_exit'], "rtn_benchmark": rtn_str}
            data1 = {"dt_enter": row['dt_enter'], "dt_exit": row['dt_exit'], "rtn": row['rtn']}
            ivv_benchmark.loc[len(ivv_benchmark)] = data
            filtered_ledger2.loc[len(filtered_ledger2)] = data1

    return


@app.callback(
    Output("ab-plot", "figure"),
    [Input('ab-range-slider', 'value'), Input("predict", "n_clicks")],
    prevent_initial_call = True
)
def render_smart_plot(slider_range, n_clicks):
    df = pd.concat([filtered_ledger2, ivv_benchmark], axis=1, join="inner")
    print(df)
    df = df[['rtn', 'rtn_benchmark']]
    for index, row in df.iterrows():
        df.at[index, 'rtn'] = float(row['rtn'].replace('%', 'e-2'))
        df.at[index, 'rtn_benchmark'] = float(row['rtn_benchmark'].replace('%', 'e-2'))

    fig = px.scatter(
        df,
        x=df.columns[1],
        y=df.columns[0],
        trendline='ols'
    )

    fit_results = px.get_trendline_results(fig).px_fit_results.iloc[0].params

    fig.update_layout(
        title = "Alpha: " + \
                str("{:.5%}".format(fit_results[0])) + "; Beta: " + \
                str(round(fit_results[1], 3)) + " for smart ledger",
        xaxis=dict(tickformat=".2%"),
        yaxis=dict(tickformat=".2%")
    )

    return(fig)



def dumb_innerJoinRtn():
    # generate IVV rtn
    print("try inner join")
    ivv_data = pd.DataFrame(columns=['dt_enter', 'dt_exit', 'rtn_benchmark'])
    ivv = helper.query_date(start_date_string, end_date_string, 'IVV')
    for index, row in ledger.iterrows():
        enter_date = row['dt_enter']
        exit_date = row['dt_exit']
        rtn_str = ""
        if enter_date != "" and exit_date != "":
            enter_price_row = ivv.loc[ivv['Date']==enter_date]
            enter_price = enter_price_row.iloc[0]['Close Price']
            # print(enter_price)
            exit_price_row = ivv.loc[ivv['Date']==exit_date]
            exit_price = exit_price_row.iloc[0]['Close Price']
            n = helper.count_bdays(enter_date, exit_date)
            if(n==0):
                print("n is 0")
            else:
                rtn = np.log(float(exit_price) / float(enter_price)) / int(n)
                rtn_str = '{:.3%}'.format(rtn)
        # ledger2.at[index, 'rtn'] = rtn_str
            data = {"dt_enter": row['dt_enter'], "dt_exit": row['dt_exit'], "rtn_benchmark": rtn_str}
            ivv_data.loc[len(ivv_data)] = data

    return ivv_data

@app.callback(
    Output("dumb-plot", "figure"),
    [Input('dumb-range-slider', 'value'), Input("predict", "n_clicks")],
    prevent_initial_call = True
)
def render_dumb_plot(slider_range, n_clicks):
    ivv_data = dumb_innerJoinRtn()
    df = pd.concat([ledger, ivv_data], axis=1, join="inner")
    print(df)
    df = df[['rtn', 'rtn_benchmark']]
    df = df[df['rtn'] != '']
    for index, row in df.iterrows():
        df.at[index, 'rtn'] = float(row['rtn'].replace('%', 'e-2'))
        df.at[index, 'rtn_benchmark'] = float(row['rtn_benchmark'].replace('%', 'e-2'))

    print(df)
    fig = px.scatter(
        df,
        x=df.columns[1],
        y=df.columns[0],
        trendline='ols'
    )

    fit_results = px.get_trendline_results(fig).px_fit_results.iloc[0].params

    fig.update_layout(
        title = "Alpha: " + \
                str("{:.5%}".format(fit_results[0])) + "; Beta: " + \
                str(round(fit_results[1], 3)),
        xaxis=dict(tickformat=".2%"),
        yaxis=dict(tickformat=".2%")
    )

    return(fig)


# @app.callback(
#     Output("predict-data", "data"), Output("actual-data", "data"),
#     Input("predict", "n_clicks"),
#     State("predict-date", "date"),
#     prevent_initial_call=True
# )
# def render_predict(n_clicks, predict_date):
#     print("predict-result for" + predict_date)
#     predict, actual = percepto.percep(predict_date)
#     print(("-----------------"))
#     print(predict)
#     print(("-----------------"))
#     print(actual)
#     # start process data
#     return predict.to_dict('records'), actual.to_dict('records')

@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "active_tab"), Input("entry", "data"), Input("ledger", "data"), Input("ledger2", "data")],
)
def render_tab_content(active_tab, entry, ledger, ledger2):
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
        elif active_tab == "Ledger2":
            return html.Div([
                dash_table.DataTable(
                    data = ledger2,
                    id="ledger2-tbl",
                    page_action='none',
                    style_table={'height': '230px', 'overflowY': 'auto'}
                ),
            ])
    return "No tab selected"

if __name__ == '__main__':
    app.run_server(debug=True)
    # serve(app)