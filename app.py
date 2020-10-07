import uuid
from flask import Flask, session, redirect, url_for
from flask_session import Session

from datetime import datetime, timedelta
import requests
import msal

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/login')
def login():
    return 'login'
    
