import uuid
import requests
from flask import Flask, render_template, session, request, redirect, url_for
from flask_session import Session  # https://pythonhosted.org/Flask-Session
from datetime import datetime, timedelta
import msal
import app_config


app = Flask(__name__)
app.config.from_object(app_config)
Session(app)

# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/1.0.x/deploying/wsgi-standalone/#proxy-setups
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template('index.html', user=session["user"], version=msal.__version__)

@app.route("/login")
def login():
    session["state"] = str(uuid.uuid4())
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    auth_url = _build_auth_url(scopes=app_config.SCOPE, state=session["state"])
    return render_template("login.html", auth_url=auth_url, version=msal.__version__)

@app.route(app_config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    if request.args.get('state') != session.get("state"):
        return redirect(url_for("index"))  # No-OP. Goes back to Index page
    if "error" in request.args:  # Authentication/Authorization failure
        return render_template("auth_error.html", result=request.args)
    if request.args.get('code'):
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.args['code'],
            scopes=app_config.SCOPE,  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=url_for("authorized", _external=True))
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        app_config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("index", _external=True))

@app.route("/graphcall")
def graphcall():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    graph_data = requests.get(  # Use token to call downstream service
        app_config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        ).json()
    return render_template('display.html', result=graph_data)

@app.route("/testToken")
def testToken():

    graph_data = requests.post(  
        "https://login.microsoftonline.com/d26bf608-8326-4a29-88fc-36e8f30b976d/oauth2/v2.0/token",
        headers={'Authorization': 'Bearer '},
        
        json =
        {
             'client_id':app_config.CLIENT_ID,
             'client_secret':app_config.CLIENT_SECRET,
             'redirect_ur':'http://localhost:5000/',
             'grant_type':'authorization_code',
             'resource':'https://graph.microsoft.com',
             'scope':app_config.SCOPE
        }
        ).json()
    return render_template('display.html', result=graph_data)


@app.route("/testToken1")
def testToken1():

    graph_data = requests.post(  
        "https://login.microsoftonline.com/organizations/oauth2/v2.0/token",
        headers={'Authorization': 'Bearer', 'Content-Type': 'application/x-www-form-urlencoded'},
        json =
        {
             'client_id':app_config.CLIENT_ID,
             'grant_type':'password',
             'username':app_config.username,
             'password':app_config.pw,
             'scope':app_config.SCOPE,
             #'client_secret':app_config.CLIENT_SECRET
             "authority": "https://login.microsoftonline.com/organizations",
             
        }
        ).json()
    return render_template('display.html', result=graph_data)

@app.route("/onlinemeeting")
def onlinemeeting():
    #token = _get_token_from_cache(app_config.SCOPE)
    token = _get_token_from_pw()
    if not token:
        return redirect(url_for("login"))
    print(token)
    
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
    return render_template('display.html', result=graph_data)


@app.route("/callrecord")
def callrecord():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    graph_data = requests.post(  
        "https://graph.microsoft.com/v1.0/me/onlineMeetings",
        headers={'Authorization': 'Bearer ' + token['access_token'],
                 'Content-type':'application/json'},
        json ={
            "startDateTime":"2020-09-30T06:42:34",
            "endDateTime":"2020-09-30T06:45:34",
            "subject":"d9a6b735-575f-44e8-99e8-b3283aaee441"
            }
        
        ).json()
    return render_template('display.html', result=graph_data)

def _convert_dt_string(datetime):
    return datetime.strftime("%Y-%m-%dT%H:%M:%S-07:00")

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app_config.CLIENT_ID, authority=authority or app_config.AUTHORITY,
        client_credential=app_config.CLIENT_SECRET, token_cache=cache)

def _build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for("authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result
    
def _get_token_from_pw():
    cache = _load_cache()
    temp1 = msal.PublicClientApplication(app_config.CLIENT_ID, authority=app_config.AUTHORITYORG)
    result = temp1.acquire_token_by_username_password(
        username=app_config.username, password=app_config.pw, data={'client_secret':app_config.CLIENT_SECRET}, scopes=app_config.SCOPE)
    session["user"] = result.get("id_token_claims")
    _save_cache(cache)
    return result
    
app.jinja_env.globals.update(_build_auth_url=_build_auth_url)  # Used in template

if __name__ == "__main__":
    app.run()

