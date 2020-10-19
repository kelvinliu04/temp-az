import uuid
from flask import Flask, session, redirect, url_for, request
from flask_session import Session
import json
from datetime import datetime, timedelta
import requests
import msal
import app_config
import threading

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/login')
def login():
    return 'login'


@app.route('/onlinemeeting')
def onlinemeeting():
    teams_url = _teams_start()
    return teams_url
    
@app.route('/onlinemeeting2')
def onlinemeeting2():
    teams_url = _teams_event()
    return teams_url

@app.route('/startonlinemeeting', methods=['POST']) #allow both GET and POST requests
def startonlinemeeting():
    req_json = request.get_json()
    if req_json['agent']:
        agent = req_json['agent']
        email = agent['email']
        name = agent['name']
        
        room_id = req_json['room_id']
        
        threading1 = threading.Thread(target=_send_button_qiscus, args=(email, name, room_id, ))
        threading1.start()
    return req_json

#----------------------------------------------------------------------------------------------------------------------------------
def _convert_dt_string(datetime):
    return datetime.strftime("%Y-%m-%dT%H:%M:%S-07:00")

def _get_token_from_pw():
    #cache = _load_cache()
    temp1 = msal.PublicClientApplication(app_config.CLIENT_ID, authority=app_config.AUTHORITYORG)
    result = temp1.acquire_token_by_username_password(
        username=app_config.username, password=app_config.pw, data={'client_secret':app_config.CLIENT_SECRET}, scopes=app_config.SCOPE)
    #session["user"] = result.get("id_token_claims")
    #_save_cache(cache)
    return result

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()
        
        
def _send_button_qiscus(email, name, room_id):
    teams_url = _teams_start()

    json = {
        	"sender_email": "gume-br1lmyldfzyvrw2j_admin@qismo.com", 
        	"message": "Hi good morning",
        	"type": "buttons",
        	"room_id": str(room_id),
        	"payload": {
        		"text": "Teams Online Meeting".format(email),
        	    "buttons": [
            	        {
        	            "label": "Join",
        	            "type": "link",
        	            "payload": {
        	                "url": "{}".format(teams_url)
        	            }
        	        }
        		]
        	} 
        }
    base_url = "https://multichannel.qiscus.com/"
    app_code = 'gume-br1lmyldfzyvrw2j'
    url = base_url + app_code + "/bot"
    headers = {'Content-Type': 'application/json'}
    result = requests.post(url, headers=headers, json=json)
    
    
def _teams_start():
    token = _get_token_from_pw()
    print(token)
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
                            "id": "30374d5c-c7df-4a1e-83f1-7d2e5e135b16"
                            }
                        }
                    }
                }
            }
        ).json()
    return graph_data['joinWebUrl']

def _teams_event():
    token = _get_token_from_pw()
    if not token:
        return redirect(url_for("login"))
    graph_data = requests.post(  
        "https://graph.microsoft.com/v1.0/users/c1141e56-e9e9-4fa7-94d5-7f84c2141bc7/events",
        headers={'Authorization': 'Bearer ' + token['access_token'],
                 'Content-type':'application/json'},
        
        json= {
              "subject": "Let's go for lunch",
              "body": {
                "contentType": "HTML",
                "content": "Does next month work for you?"
              },
              "isOnlineMeeting": True,
              "onlineMeetingProvider": "teamsForBusiness"
            }
        ).json()
    return graph_data
    

                  
if __name__ == "__main__":
    app.run()

#9dad4a29-78bf-4ad5-8e65-7be53fb88933