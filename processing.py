import pandas as pd
import numpy as np
import base64
import dash_html_components as html
import io

pd.options.mode.chained_assignment = None  # default='warn'; to disable warning of setting value on copy of dataframe


def parse_data(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.DataFrame()  # is it really necessary to reference local variable before assignment?
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div(['There was an error processing this file.'])
    return df


def data_processing(df):
    """
    Makes all necessary 'dirty' work with data: types conversion, manipulations with columns/rows etc.
    """
    df['Time'] = df['requestdate'].str[:14] + '00:00'
    df['requestdate'] = pd.to_datetime(df['requestdate'])
    df['hour'] = df['requestdate'].dt.hour
    df['day'] = df['requestdate'].dt.day
    df['month'] = df['requestdate'].dt.month
    df = df.sort_values(by=['day'], ascending=False).reset_index(drop=True)

    df['refresh_OK'] = np.where((df.SessionSource == 'RefreshActiveAccounts') &
                                (df.SessionStatus.isin(['Finished', 'TransactionDetails'])) &
                                (df.Stage.isin(['Transactions', 'TransactionDetails']).any()), 1, 0)
    df['refresh_NOK'] = np.where((df.SessionSource == 'RefreshActiveAccounts') &
                                 (df.SessionStatus == 'Failed') &
                                 (df.Stage != 'TransactionDetails'), 1, 0)  # new condition
    df['batch_OK'] = np.where((df.SessionSource == 'Batch') & (df.SessionStatus == 'Finished') & (
        df.Stage.isin(['Transactions', 'TransactionDetails'])), 1, 0)
    df['batch_all'] = np.where((df.SessionSource == 'Batch'), 1, 0)
    df['batch_NOK_accounts'] = np.where(
        (df.SessionSource == 'Batch') & (df.SessionStatus == 'Failed') & (df.Stage == 'Accounts'), 1, 0)  # ?
    df['batch_NOK_trx'] = np.where((df.SessionSource == 'Batch') & (df.SessionStatus == 'Failed') & (
        df.Stage.isin(['Transactions', 'TransactionDetails'])), 1, 0)
    df['authorize_OK'] = np.where((df.SessionSource == 'Authorize') & (df.SessionStatus == 'Finished') & (
        df.Stage.isin(['Transactions', 'TransactionDetails'])), 1, 0)
    df['authorize_all'] = np.where((df.SessionSource == 'Authorize'), 1, 0)
    df['unfinished_SCA'] = np.where(
        (df.SessionSource == 'Authorize') & (df.SessionStatus == 'Expired') & (df.Stage == 'Authentication '), 1, 0)
    df['SCA_NOK'] = np.where(
        (df.SessionSource == 'Authorize') & (df.SessionStatus == 'Failed') & (df.Stage != 'TransactionDetails'), 1, 0)
    df['TrxDetails_NOK'] = np.where((df.SessionStatus == 'Failed') & (df.Stage == 'TransactionDetails'), 1, 0)
    df['SCA_all'] = np.where((df.SessionSource == 'Authorize'), 1, 0)  # the same as 'authorize_all' column
    df['RefreshActiveAccounts'] = np.where((df.SessionSource == 'RefreshActiveAccounts'), 1, 0)
    df['DeleteConsent'] = np.where((df.SessionSource == 'DeleteConsent'), 1, 0)

    df['batch_12_AM_all'] = np.where((df.SessionSource == 'Batch') & (df.hour == 12), 1, 0)
    df['batch_12_AM_NOK'] = np.where(
        (df.SessionSource == 'Batch') & (df.hour == 12) & (df.SessionStatus == 'Failed'), 1, 0)
    df['batch_6_AM_all'] = np.where((df.SessionSource == 'Batch') & (df.hour == 6), 1, 0)
    df['batch_6_AM_NOK'] = np.where((df.SessionSource == 'Batch') & (df.hour == 6) & (df.SessionStatus == 'Failed'),
                                    1, 0)
    df['batch_12_PM_all'] = np.where((df.SessionSource == 'Batch') & (df.hour == 0), 1, 0)
    df['batch_12_PM_NOK'] = np.where(
        (df.SessionSource == 'Batch') & (df.hour == 0) & (df.SessionStatus == 'Failed'), 1, 0)
    df['batch_6_PM_all'] = np.where((df.SessionSource == 'Batch') & (df.hour == 18), 1, 0)
    df['batch_6_PM_NOK'] = np.where(
        (df.SessionSource == 'Batch') & (df.hour == 18) & (df.SessionStatus == 'Failed'), 1, 0)
    return df


def main_callback(df, filename, ecosystem, select_condition):
    import dash_table
    import dash_core_components as dcc
    import plotly.graph_objects as go

    df['unique_id'] = df['Id'] + '_' + ecosystem
    df['ecosystem'] = ecosystem
    df['requestdate'] = df['requestdate'].astype(str)

    data = df.copy()

    # ------- data for database -------
    db = df.copy()
    db = db.to_json(date_format='iso', orient='split')

    # huge data processing step
    df = data_processing(df)

    # ------- processing of 'report' tab -------
    final_report = report(df)

    # ------- processing of 'chart' tab -------
    df_plot = chart(df)

    # ------- processing of 'summary' tab -------
    summary_main, summary_bank, byhours = summary(df)

    data = html.Div([
        html.Hr() if select_condition else html.H6(filename),
        dash_table.DataTable(
            data=data.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in data.columns],
            filter_action='native',  # filter option
            sort_action='native',
            sort_mode='single',
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ])

    report_table = html.Div([
        html.Div([
            html.Hr(),
            dash_table.DataTable(
                data=final_report.to_dict('rows'),
                columns=[{'name': i, 'id': i} for i in final_report.columns],
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                }
            )
        ])
    ])

    graph = html.Div([
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='bank-name',
                    options=[

                    ],
                    value='NYC'
                ),
            ], className='two columns'),
            html.Div([
                dcc.Dropdown(
                    id='dropdown2',
                    options=[

                    ],
                    value='NYC'
                ),
            ], className='two columns'),
            html.Div([
                # slider for choosing time range here?
            ])
        ], className='row'),
        html.Hr(),
        dcc.Graph(
            id='graph',
            figure={
                'data': [
                    go.Bar(name='Authorize', x=df_plot.Time, y=df_plot.authorize_all),
                    go.Bar(name='Batch', x=df_plot.Time, y=df_plot.batch_all),
                    go.Bar(name='DeleteConsent', x=df_plot.Time, y=df_plot.DeleteConsent),
                    go.Bar(name='RefreshActiveAccounts', x=df_plot.Time, y=df_plot.RefreshActiveAccounts)
                ],
                'layout': go.Layout(title='', barmode='group')
            }
        )
    ])

    summary_table = html.Div([
        html.Div([
            html.Div([
                html.Hr(),
                dash_table.DataTable(
                    # small table
                    data=summary_main.to_dict('rows'),
                    columns=[{'name': i, 'id': i} for i in summary_main.columns],
                    style_data_conditional=[
                        # {
                        #     'if': {'row_index': 'odd'},
                        #     'backgroundColor': 'rgb(248, 248, 248)'
                        # }
                    ],
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    }
                ),
                html.Hr()
            ], className='two columns'),
            html.Div([
                html.Hr(),
                dash_table.DataTable(
                    data=summary_bank.to_dict('rows'),
                    columns=[{'name': i, 'id': i} for i in summary_bank.columns],
                    style_data_conditional=[
                        {
                            'if': {'column_id':
                                       ['refresh_NOK', 'batch_NOK_accounts', 'batch_NOK_trx', 'SCA_NOK',
                                        'batch_%_NOK', 'unfinished_SCA_%']},
                            'backgroundColor': '#ffe6e6'
                        },
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    }
                )
            ], className='ten columns')
        ], className='row'),
        html.Div([
            html.Div([
                dash_table.DataTable(
                    data=byhours.to_dict('rows'),
                    columns=[{'name': i, 'id': i} for i in byhours.columns],
                    style_data_conditional=[
                        {
                            'if': {'column_id':
                                       ['batch_12_AM_NOK', 'batch_12_AM_%', 'batch_6_AM_NOK', 'batch_6_AM_%',
                                        'batch_12_PM_NOK', 'batch_12_PM_%', 'batch_6_PM_NOK', 'batch_6_PM_%']},
                            'backgroundColor': '#ffe6e6'
                        }
                    ],
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    }
                )
            ])
        ], className='row')
    ])

    return data, report_table, graph, summary_table, db


def select_from_db(query):
    import mysql.connector
    import sshtunnel

    sshtunnel.SSH_TIMEOUT = 5.0
    sshtunnel.TUNNEL_TIMEOUT = 5.0

    with sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username='apihub', ssh_password='Pass123',
            remote_bind_address=('apihub.mysql.pythonanywhere-services.com', 3306)
    ) as tunnel:
        mydb = mysql.connector.connect(
            user='apihub', password='Pass123',
            host='127.0.0.1', port=tunnel.local_bind_port,
            database='apihub$sessions'
        )
        # print(mydb)
        mycursor = mydb.cursor()
        myquery = str(query)
        mycursor.execute(myquery)
        myresult = mycursor.fetchall()
        # mycursor.close()  # not necessary here
        mydb.close()
        mydata = pd.DataFrame(myresult)
        colnames = ['requestdate', 'externaluserid', 'count_useraccounts_in_bank', 'SessionStatus', 'Stage',
                    'SessionSource', 'failuremessageid', 'accountsfetchedcount', 'accountsprocessedcount', 'BankName',
                    'AspspResponseContent', 'AspspResponseStatus', 'ConsentId', 'ErrorMessage', 'ErrorType',
                    'ExecutionId', 'TransactionStatus', 'TransactionStatusTimestamp', 'Id', 'unique_id', 'ecosystem']
        mydata.columns = colnames
        return mydata


def insert_to_db(df):
    import mysql.connector
    import sshtunnel

    sshtunnel.SSH_TIMEOUT = 5.0
    sshtunnel.TUNNEL_TIMEOUT = 5.0

    with sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username='apihub', ssh_password='Pass123',
            remote_bind_address=('apihub.mysql.pythonanywhere-services.com', 3306)
    ) as tunnel:
        mydb = mysql.connector.connect(
            user='apihub', password='Pass123',
            host='127.0.0.1', port=tunnel.local_bind_port,
            database='apihub$sessions'
        )
        print(mydb)
        mycursor = mydb.cursor()
        df['requestdate'] = df['requestdate'].astype(str).str[:22]
        df = df.fillna('')  # need it to "counter" NaN values in 'failuremessageid'
        input_df = [tuple(x) for x in df.values]
        sql_query = 'INSERT IGNORE INTO report ' \
                    '(requestdate, externaluserid, count_useraccounts_in_bank, SessionStatus, Stage, SessionSource,' \
                    'failuremessageid, accountsfetchedcount, accountsprocessedcount, BankName,' \
                    'AspspResponseContent, AspspResponseStatus, ConsentId, ErrorMessage, ErrorType, ExecutionId,' \
                    'TransactionStatus, TransactionStatusTimestamp, Id, unique_id, ecosystem)' \
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,' \
                    '%s)'  # N\'%s\'
        # print(sql_query)
        mycursor.executemany(sql_query, input_df)
        mydb.commit()
        mydb.close()


def report(df):
    report = df.copy()

    report['Authorize'] = np.where((df.SessionSource == 'Authorize'), 1, 0)
    report['Batch'] = np.where((df.SessionSource == 'Batch'), 1, 0)
    report['DeleteConsent'] = np.where((df.SessionSource == 'DeleteConsent'), 1, 0)
    report['RefreshActiveAccounts'] = np.where((df.SessionSource == 'RefreshActiveAccounts'), 1, 0)

    aggregations = {
        'Authorize': sum,
        'Batch': sum,
        'DeleteConsent': sum,
        'RefreshActiveAccounts': sum
    }
    myreport = report.groupby(['month', 'day', 'hour']).agg(aggregations)
    myreport.loc['Total'] = myreport.sum()  # add total row
    myreport['Total'] = myreport.sum(axis=1)  # add total column
    myreport['Time'] = myreport.index  # reassign index
    final_report = myreport.copy()

    # ------------------------------------------------------------------------
    df['year'] = df['requestdate'].dt.year
    year = df['year'][0]
    # think of more convenient way of getting this column
    for i in range(0, len(final_report)):
        delimiter = f'{year}-0' if len(str(final_report.index[i][0])) == 1 else f'{year}-'
        delimiter2 = '-0' if len(str(final_report.index[i][1])) == 1 else '-'
        final_report['Time'].iloc[i] = delimiter + str(final_report.index[i][0]) + delimiter2 + str(
            final_report.index[i][1]) + ' ' + str(final_report.index[i][2]) + ':00:00'
    # ------------------------------------------------------------------------

    final_report = final_report.iloc[:, list(range(-1, 5))].reset_index(drop=True)
    final_report['Time'][len(final_report) - 1] = 'Total'
    return final_report


def chart(df):
    df_plot = df[['Time', 'BankName', 'SessionStatus', 'Stage', 'SessionSource', 'authorize_all', 'batch_all',
                  'RefreshActiveAccounts', 'DeleteConsent']]
    df_plot = df_plot.sort_values(by=['Time'], ascending=False).reset_index(drop=True)
    return df_plot


def summary(df):
    unique_userid = len(df['externaluserid'].unique()) if 'externaluserid' in df.columns else 'n/a'
    sessions_number = len(df)
    successful_refresh_sessions = \
        len(df[(df.SessionSource == 'RefreshActiveAccounts') & (df.SessionStatus == 'Finished') &
               (df.Stage.isin(['Transactions', 'TransactionDetails']))])
    refresh_sessions_all = len(df[df.SessionSource == 'RefreshActiveAccounts'])
    successful_account_added = len(df[(df.SessionSource == 'Authorize') & (df.SessionStatus == 'Finished') &
                                      (df.Stage.isin(['Transactions', 'TransactionDetails']))])
    unfinished_sca = len(df[(df.SessionSource == 'Authorize') & (df.SessionStatus == 'Expired')])
    error_sca = len(df[(df.SessionSource == 'Authorize') & (~df.SessionStatus.isin(['Finished', 'Expired']))])
    all_sca = len(df[df.SessionSource == 'Authorize'])
    batch_ok = len(df[(df.SessionSource == 'Batch') & (df.SessionStatus == 'Finished') &
                      (df.Stage.isin(['Transactions', 'TransactionDetails']))])
    batch_all = len(df[df.SessionSource == 'Batch'])

    # small table in summary tab
    summary_main = \
        pd.DataFrame({'unique userID': unique_userid, 'sessions number': sessions_number,
                      'successful refresh_sessions': successful_refresh_sessions,
                      'refresh sessions all': refresh_sessions_all,
                      'successful account added': successful_account_added,
                      'unfinished SCA': unfinished_sca, 'error SCA': error_sca,
                      'all SCA': all_sca, 'batch OK': batch_ok, 'batch all': batch_all}, index=['Total']).T

    summary_main = pd.DataFrame({'': summary_main.index, 'Total': summary_main.Total})

    aggregations_bank = {
        'refresh_OK': sum,
        'refresh_NOK': sum,
        'batch_OK': sum,
        'batch_all': sum,
        'batch_NOK_accounts': sum,
        'batch_NOK_trx': sum,
        'authorize_OK': sum,
        'authorize_all': sum,
        'unfinished_SCA': sum,
        'SCA_NOK': sum,
        'SCA_all': sum,
        'TrxDetails_NOK': sum
    }
    summary_bank = df.groupby('BankName').agg(aggregations_bank)
    summary_bank['batch_%_NOK'] = np.where(summary_bank.batch_all > 0, round(
        ((summary_bank.batch_NOK_accounts + summary_bank.batch_NOK_trx) / summary_bank.batch_all) * 100, 1), 'n/a')
    summary_bank['unfinished_SCA_%'] = np.where(summary_bank.SCA_all > 0,
                                                round((summary_bank.unfinished_SCA / summary_bank.SCA_all) * 100,
                                                      1), 'n/a')
    summary_bank.loc['Total'] = summary_bank.sum()
    summary_bank['bank'] = summary_bank.index
    summary_bank = summary_bank.iloc[:, list(range(-1, 14))].reset_index(drop=True)
    summary_bank.at[len(summary_bank) - 1, ['batch_%_NOK', 'unfinished_SCA_%']] = ''

    byhours = df.copy()

    aggregations_hours = {
        'batch_12_AM_all': sum,
        'batch_12_AM_NOK': sum,
        'batch_6_AM_all': sum,
        'batch_6_AM_NOK': sum,
        'batch_12_PM_all': sum,
        'batch_12_PM_NOK': sum,
        'batch_6_PM_all': sum,
        'batch_6_PM_NOK': sum,
    }
    byhours = byhours.groupby('BankName').agg(aggregations_hours)
    byhours.loc['Total'] = byhours.sum()  # add total row
    byhours['batch_12_AM_%'] = round(byhours['batch_12_AM_NOK'] / byhours['batch_12_AM_all'], 2)
    byhours['batch_6_AM_%'] = round(byhours['batch_6_AM_NOK'] / byhours['batch_6_AM_all'], 2)
    byhours['batch_12_PM_%'] = round(byhours['batch_12_PM_NOK'] / byhours['batch_12_PM_all'], 2)
    byhours['batch_6_PM_%'] = round(byhours['batch_6_PM_NOK'] / byhours['batch_6_PM_all'], 2)
    byhours['bank'] = byhours.index
    byhours = \
        byhours[['bank', 'batch_12_AM_all', 'batch_12_AM_NOK', 'batch_12_AM_%', 'batch_6_AM_all',
                 'batch_6_AM_NOK', 'batch_6_AM_%', 'batch_12_PM_all', 'batch_12_PM_NOK', 'batch_12_PM_%',
                 'batch_6_PM_all', 'batch_6_PM_NOK', 'batch_6_PM_%']].reset_index(drop=True)
    byhours.at[len(byhours) - 1, ['batch_12_AM_%', 'batch_6_AM_%', 'batch_12_PM_%', 'batch_6_PM_%']] = ''

    return summary_main, summary_bank, byhours
