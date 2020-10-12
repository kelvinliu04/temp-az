import uuid
from flask import Flask, session, redirect, url_for, request
from flask_session import Session
import json
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

@app.route('/test', methods=['POST']) #allow both GET and POST requests
def form_example():
    if request.method == 'POST':  #this block is only entered when the form is submitted
        req_json = request.get_json()
        #req_json = json.loads(request.data, strict=False)
        data1 = req_json["data1"]
        data2 = req_json["data2"]
        #data1 = req_json.get("data1")
        #data2 = req_json.get("data2")

        #return 'post {} {} '.format(data1, data2)
        #return json.loads({'contents': data2, 'appname':data1})
        return {"result":"ok"}
    else:
        return 'get'
    

@app.route('/post', methods=['POST']) #allow both GET and POST requests
def post1():
    req_json = request.get_json()
    #data = req_json["data"]
    return req_json

@app.route('/startonlinemeeting', methods=['POST']) #allow both GET and POST requests
def post1():
    req_json = request.get_json()
    if req_json['payload']:
        pl = req_json['payload']
        email = pl['from']['email']
        name = pl['from']['name']
        room_id = pl['room']['id']
        json = {
            	"sender_email": "tyes-razurkhhoyewouxd_admin@qismo.com", 
            	"message": "Hi good morning"+str(email),
            	"type": "buttons",
            	"room_id": room_id,
            	"payload": {
            		"text": "silahkan pencet",
            	    "buttons": [
            	        {
            	            "label": "button1",
            	            "type": "postback",
            	            "payload": {
            	                "url": "https://qiscus-online-meeting.azurewebsites.net/",
            	                "method": "get",
            	                "payload": None
            	            }
            	        },
            	        {
            	            "label": "button2",
            	            "type": "link",
            	            "payload": {
            	                "url": "https://qiscus-online-meeting.azurewebsites.net/login"
            	            }
            	        }
            		]
            	}
            }
        base_url = "https://multichannel.qiscus.com/"
        app_code = 'tyes-razurkhhoyewouxd'
        url = base_url + app_code + "/bot"
        headers = {'Content-Type': 'application/json'}
        result = requests.post(url, headers=headers, json=json)
        #data = req_json["data"]
    return req_json

#----------------------------------------------------------------------------------------------------------------------------------
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
        
        
        
        
        

                  
#if __name__ == "__main__":
    #app.run()
