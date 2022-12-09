from dash import Dash, html, dcc, Input, Output
import pandas as pd
import sqlite3
import plotly.express as px
import datetime

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


conn = get_db_connection()
df = pd.read_sql_query('select * from coins', conn)
df.drop('index', axis=1, inplace=True)

conn.close()



app.layout = html.Div([
    html.Div([

        html.H1('Cryptocurrency Price Predictions'),

        html.Div([
            dcc.Dropdown(
                df['coin'],
                df['coin'].iloc[0],
                id='coin-selector',
            ),
            dcc.RadioItems(
                ['LSTM', 'Transformer', 'DLinear'],
                'LSTM',
                id='model-selector',
                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
            ),
            dcc.RadioItems(
                ['1 Day', '2 Day', '3 Day', '4 Day', '5 Day', '6 Day', '7 Day'],
                '1 Day',
                id='days-predicted',
                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
            )
        ],
        style={'width': '49%', 'display': 'inline-block'}),
    ], style={
        'padding': '10px 5px'
    }),

    html.Div([
        dcc.Graph(id='current-preds', style={"margin-top": "10px", "margin-bottom": "10px"}),
        dcc.Graph(id='pred-history'),
    ], style={'display': 'inline-block', 'width': '49%'}),

    html.Footer([
        html.H2('For more information about this project, please see details here:   ', 
                style={'display': 'inline-block', 'padding' : '10px'}), 

        html.A(html.Img(src = app.get_asset_url('github-mark.png'), style = {'width': '40px', 'height' : 'auto'}), 
            href = 'https://github.com/camdenhine')
        ])
])


def create_time_series(dff, title, graph_type, days=1):

    if graph_type=='preds':
        y='predictions'
    elif graph_type=='history':
        y=['Day_'+str(days), 'Close']

    fig = px.scatter(dff, x='Date', y=y)

    if graph_type == 'preds':
        fig.update_traces(mode='lines+markers')

    elif graph_type == 'history':
        fig.update_traces(mode='lines')


    fig.update_xaxes(showgrid=False)

    fig.add_annotation(x=0, y=1, xanchor='left', yanchor='bottom',
                       xref='paper', yref='paper', showarrow=False, align='left',
                       text=title)

    fig.update_layout(height=300, margin={'l': 20, 'b': 30, 'r': 10, 't': 20})

    return fig


@app.callback(
    Output('current-preds', 'figure'),
    Input('coin-selector', 'value'),
    Input('model-selector', 'value'))
def update_current_preds(coin, model):
    s = model[:1]
    conn = get_db_connection()
    temp = pd.read_sql_query('select * from ' + coin + '_preds_' + s, conn)
    temp.drop('index', axis=1, inplace=True)
    ar = temp.drop(['Date', 'Close'], axis=1).iloc[-1].values
    today = pd.to_datetime(temp['Date'].iloc[-1])
    one_week = today + datetime.timedelta(days=7)
    dates = pd.date_range(today, one_week)
    dates = dates[1:]
    dates = dates.date
    current_predictions = pd.DataFrame(ar, columns = ['predictions'])
    current_predictions['Date'] = pd.Series(dates)

    title = 'Current Predictions of ' +  coin + ' using the ' + model + ' model, last updated: ' + str(today.date())
    conn.close()

    return create_time_series(current_predictions, title, graph_type='preds')


@app.callback(
    Output('pred-history', 'figure'),
    Input('coin-selector', 'value'),
    Input('model-selector', 'value'),
    Input('days-predicted', 'value'))
def update_history(coin, model, days):
    days = int(days[0])
    s = model[:1]
    conn = get_db_connection()
    temp = pd.read_sql_query('select * from ' + coin + '_preds_' + s, conn)
    temp.drop('index', axis=1, inplace=True)
    date = temp['Date'].iloc[7:].reset_index(drop=True)
    close = temp['Close'].iloc[7:].reset_index(drop=True)
    preds = temp['Day_' + str(days)].iloc[7-days:-days].reset_index(drop=True)
    hist = pd.DataFrame(date)
    hist['Close'] = close
    hist['Day_' + str(days)] = preds

    title = 'Historical Predictions of ' +  coin + ' using the ' + model + ' model ' + str(days) + ' days prior'
    conn.close()

    return create_time_series(hist, title, graph_type='history', days=days)


if __name__ == '__main__':
    app.run_server(debug=True)