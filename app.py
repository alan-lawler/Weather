import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_leaflet as dl
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime
import requests
import io

app = dash.Dash(__name__, prevent_initial_callbacks=True, title='...')

app.layout = html.Div([
    html.Nav([
        html.Img(src='...logo.png'),
        html.H2('')
    ], className='navbar'),
    html.Section([
        html.Div([
            html.H2('Model Controls'),
            html.Hr(),
            html.H3('Select a date range:'),
            dcc.DatePickerRange(
                id='dates',
                min_date_allowed=datetime(1981, 1, 1),
                max_date_allowed=datetime(2021, 1, 19),
                start_date=datetime(2020, 3, 1),
                end_date=datetime(2020, 10, 1)
            )
        ]),
        html.Div([
            html.H3('Select an option: '),
            dcc.Checklist(
                id='checklist',
                options=[
                    {'label': 'v10', 'value': 'northward_wind_at_10_metres'},
                    {'label': 'u10', 'value': 'eastward_wind_at_10_metres'}
                ],
                value=['northward_wind_at_10_metres']
                # labelStyle={'display': 'inline-block'}
            )
        ]),
        html.Button(
            id='submit-button',
            n_clicks=0,
            children='Submit'
            # style={'fontSize': 24, 'marginLeft': '30px'}
        ),
    ], className='menu'),
    html.Section([
        html.Div([
            html.H3('Select a location on the map:'),
            html.A('Coordinates: '),
            html.A(id='coordinates'),
        ]),
        html.Div([
            dl.Map([dl.TileLayer(), dl.LayerGroup(id="layer")],
                   id="map",
                   center=(33, -91),
                   zoom=4
                   )
        ], className='map'),
    ], className='location-container'),
    html.Section([
        html.Div([
            dcc.Graph(id='graph')
        ])
    ], className='chart'),
])


# https://dash-leaflet.herokuapp.com/#map_click
@app.callback(Output("layer", "children"),
              [Input("map", "click_lat_lng")])
def map_click(click_lat_lng):
    return [dl.Marker(position=click_lat_lng, children=dl.Tooltip("({:.3f}, {:.3f})".format(*click_lat_lng)))]


@app.callback(Output('coordinates', 'children'),
              [Input('map', 'click_lat_lng')])
def click_coord(cord):
    x = float(cord[0])
    y = float(cord[1])
    return f'({x:.3f}, {y:.3f})'


@app.callback(Output('graph', 'figure'),
              [Input('submit-button', 'n_clicks')],
              [State('map', 'click_lat_lng'),
               State('dates', 'start_date'),
               State('dates', 'end_date'),
               State('checklist', 'value')])
def update_graph(n_clicks, cord, start_date, end_date, var):
    start = datetime.strptime(start_date[:10], '%Y-%m-%d')
    end = datetime.strptime(end_date[:10], '%Y-%m-%d')
    traces = []

    if len(var) == 2:
        for value in var:
            data = api_call(value, cord, start, end)
            traces.append(go.Scatter(
                x=data['axis:time'],
                y=data['data:' + value],
                mode='lines',
                name=value
            ))
    else:
        var = str(var[0])
        data = api_call(var, cord, start, end)
        traces.append(go.Scatter(
            x=data['axis:time'],
            y=data['data:' + var],
            mode='lines',
            name=var
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(title='Wind Speed',
                      xaxis_title='Dates',
                      yaxis_title='Wind Speed at 10m')
    return fig


def api_call(var, cord, start_date, end_date):
    apikey = 'apikey=...'
    base_url = 'https://api.planetos.com/v1/datasets/'
    dataset = 'ecmwf_era5_v2'
    lat = cord[0]
    lon = cord[1]
    start = str(start_date)[:10] + 'T00:00:00Z'
    end = str(end_date)[:10] + 'T23:59:59Z'
    endpoint_path = f'{dataset}/point?var={var}&lat={lat}&lon={lon}&start={start}&end={end}&{apikey}' \
                    f'&max_count=True&count=10000&csv=True&z=all'
    endpoint = f'{base_url}{endpoint_path}'
    data = requests.get(endpoint).content
    df = pd.read_csv(io.StringIO(data.decode('utf-8')))
    return df


if __name__ == '__main__':
    app.run_server()
