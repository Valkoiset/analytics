import dash
import dash_auth
import flask
import os
from os.path import join, dirname
from dotenv import load_dotenv


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

LOGIN = os.environ.get('LOGIN')
PASS = os.environ.get('PASS')
VALID_USERNAME_PASSWORD_PAIRS = {LOGIN: PASS}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']  # default from documentation

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = 'analytics'
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)
