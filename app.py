import uuid
from flask import Flask, session, redirect, url_for
from flask_session import Session

from datetime import datetime, timedelta
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
    
@app.route("/onlinemeeting")
def onlinemeeting():
    token = _get_token_from_pw()
    if not token:
        return redirect(url_for("login"))
    
    duration = 10 # in minutes
    startDT = datetime.utcnow() - timedelta(hours=7)
    endDT = startDT + timedelta(minutes=duration)

    graph_data = requests.post(  
        "https://graph.microsoft.com/v1.0/me/onlineMeetings",
        headers={'Authorization': 'Bearer ' + token['access_token'],
                 'Content-type':'application/json'},
        
        json ={
            #"autoAdmittedUsers":"everyone",
            "startDateTime":_convert_dt_string(startDT),
            "endDateTime":_convert_dt_string(endDT),
            "participants": {
                "organizer": {
                    "identity": {
                        "user": {
                            "id": "9dad4a29-78bf-4ad5-8e65-7be53fb88933"
                            }
                        }
                    }
                }
            }
        
        ).json()
    return graph_data


def _convert_dt_string(datetime):
    return datetime.strftime("%Y-%m-%dT%H:%M:%S-07:00")

def _get_token_from_pw():
    cache = _load_cache()
    temp1 = msal.PublicClientApplication(app_config.CLIENT_ID, authority=app_config.AUTHORITYORG)
    result = temp1.acquire_token_by_username_password(
        username=app_config.username, password=app_config.pw, data={'client_secret':app_config.CLIENT_SECRET}, scopes=app_config.SCOPE)
    #session["user"] = result.get("id_token_claims")
    _save_cache(cache)
    return result

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache
def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

if __name__ == "__main__":
    app.run()