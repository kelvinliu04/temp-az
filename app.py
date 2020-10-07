import uuid
from flask import Flask, session, redirect, url_for
from flask_session import Session

import requests
import msal
import app_config

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/login')
def login():
    return 'login'
    

