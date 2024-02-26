import dash_html_components as html
import dash_core_components as dcc
from app import app

app.layout = html.Div([
    dcc.Tabs(
        id='tabs-with-classes',
        value='tab-1',
        parent_className='custom-tabs',
        className='custom-tabs-container',
        children=[
            dcc.Tab(
                label='dane',
                value='tab-1',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ', html.A('Select Files')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        # allow multiple files to be uploaded
                        multiple=True
                    ),
                    dcc.RadioItems(
                        id='ecosystem',
                        options=[
                            {'label': 'KBC', 'value': 'KBC'},
                            {'label': 'FIN', 'value': 'FIN'},
                            {'label': 'SNT', 'value': 'SNT'}
                        ],
                        value='KBC',
                        labelStyle={'display': 'inline-block'}
                    ),
                    html.Div([
                        html.Div([
                            dcc.Input(
                                id='query-input',
                                type='text',
                                placeholder='select * from report',
                                style={'width': '90%', 'display': 'table-cell', 'padding': 5, 'verticalAlign': 'middle'}
                            )
                        ], className='six columns'),
                        html.Div([
                            html.Button('run query', id='run-query', n_clicks=0)
                        ], className='two columns'),
                        html.Div([
                            html.Button('Insert data to db', id='insert-to-db', n_clicks=0, style={'display': 'block'})
                        ], className='two columns')
                    ], className='row'),
                    # hidden placeholders for storing data which is further loaded to db with click on button
                    html.P(id='data-for-db', style={'display': 'none'}),
                    html.P(id='stored-in-db', style={'display': 'none'}),
                    html.Div(id='output-data-upload')
                ]
            ),
            dcc.Tab(
                label='report',
                value='tab-2',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    html.Div(id='output-report')
                ]
            ),
            dcc.Tab(
                label='chart',
                value='tab-3', className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    # dcc.Dropdown(
                    #         id='demo-dropdown',
                    #         options=[
                    #             # {'name': i, 'id': i} for i in final_report.columns
                    #             # {'label': i, 'value': i} for i in dataframe().columns  # doesn't work yet
                    #             # {'label': 'Montreal', 'value': 'MTL'},
                    #             # {'label': 'San Francisco', 'value': 'SF'}
                    #         ],
                    #         value='NYC'
                    #     ),
                    html.Div(id='output-chart')
                ]
            ),
            dcc.Tab(
                label='summary',
                value='tab-4',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    html.Div(id='output-summary')
                ]
            )
        ]),
    html.Div(id='tabs-content-classes')
])
