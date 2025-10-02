from flask import Flask, render_template, request, redirect, url_for, session
import os
from contextlib import contextmanager
from flask import current_app
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
import db
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth

# Load .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET") 

with app.app_context():
    db.setup(app)

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=os.environ.get("AUTH0_CLIENT_ID"),
    client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect(url_for("index"))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "Anonymous")
        message = request.form.get("message", "")

        with db.get_db_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO guestbook (name, message) VALUES (%s, %s);",
                (name, message),
            )
        return redirect("/") 

    with db.get_db_cursor() as cur:
        cur.execute("SELECT name, message FROM guestbook ORDER BY created_at DESC;")
        guests = cur.fetchall()

    return render_template("guest_form.html", name=None, guests=guests)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + os.environ.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": os.environ.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )
