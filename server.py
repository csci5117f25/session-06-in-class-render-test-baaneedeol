from flask import Flask, render_template, request, redirect
import os
from contextlib import contextmanager
from flask import current_app
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
import db

load_dotenv()  

app = Flask(__name__)

with app.app_context():
    db.setup(app)
    
# @app.route('/')
# @app.route('/<name>')
# def hello(name=None):
#     return render_template('guest_form', name=name)

@app.route('/', methods = ["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        message = request.form["message"]

        with db.get_db_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO guestbook (name, message) VALUES (%s, %s);",
                (name, message),
            )
        return redirect("/") 

    with db.get_db_cursor() as cur:
        cur.execute("SELECT name, message FROM guestbook ORDER BY created_at DESC;")
        guests = cur.fetchall()

    return render_template("guest_form.html", guests=guests)
