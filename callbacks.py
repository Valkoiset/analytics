import dash
import dash_table  # important to have it here to avoid that bug with infinte "Uploading..."
import dash_html_components as html
from dash.dependencies import Input, Output, State
from app import app
from processing import parse_data, insert_to_db, main_callback, select_from_db
import pandas as pd
import time


# callback for updating accessibility of 'insert to db' button after query from db
@app.callback(
    Output('insert-to-db', 'style'),
    [Input('run-query', 'n_clicks'),
     Input('upload-data', 'contents'),
     Input('query-input', 'value')])  # query
def update_insert_to_db_button(n_clicks, contents, query):
    triggered = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if query and 'run-query' in triggered:
        return {'display': 'none'}
    elif contents or not query:
        return {'display': 'block'}


@app.callback([
    Output('stored-in-db', 'children')],
    [Input('insert-to-db', 'n_clicks'),
     Input('data-for-db', 'children')])  # stored_json_data
def update_database(n_clicks, stored_json_data):
    # very important to check if the button was triggered again, otherwise the dataset loads to db even though
    # button was clicked only once in order to load 1st dataset and wasn't clicked for 2nd
    triggered = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'insert-to-db' not in triggered:
        return ['no clicks yet']
    else:
        if n_clicks and stored_json_data:
            db = pd.read_json(stored_json_data, orient='split')
            start = time.monotonic()
            insert_to_db(db)
            finish = time.monotonic()
            print(f'data have been inserted to db in {finish - start}')
            return ['data has been uploaded']
        else:
            return ['no clicks yet']


# take input csv/xls file and make output to each tab
@app.callback([
    Output('output-data-upload', 'children'),
    Output('output-report', 'children'),
    Output('output-chart', 'children'),
    Output('output-summary', 'children'),
    Output('data-for-db', 'children')],
    [Input('upload-data', 'contents'),
     Input('ecosystem', 'value'),
     Input('query-input', 'value'),
     Input('run-query', 'n_clicks')],
    [State('upload-data', 'filename')])
def multi_output(contents, ecosystem, query, n_clicks, filename):
    # declare output variables
    db = None
    data = None
    graph = None
    report_table = html.Div()
    summary_table = html.Div()

    triggered = [p['prop_id'] for p in dash.callback_context.triggered][0]
    select_condition = query and 'run-query' in triggered

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)
        data, report_table, graph, summary_table, db = main_callback(df, filename, ecosystem, select_condition)

    if select_condition:
        try:
            start = time.monotonic()
            df = select_from_db(query)  # load data from db with sql query
            finish = time.monotonic()
            # select * from report (2.865 rows) = 4s
            print(f'data have been queried from db in {finish - start}')
            start = time.monotonic()
            data, report_table, graph, summary_table, db = main_callback(df, filename, ecosystem, select_condition)
            finish = time.monotonic()
            print(f'main_callback has been run in {finish - start}')
        except Exception as e:
            print(e)

    # all outputs at the same time!
    return data, report_table, graph, summary_table, db
