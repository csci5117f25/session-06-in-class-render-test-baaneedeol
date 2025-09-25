from flask import Flask, render_template, request, redirect
import os
from contextlib import contextmanager
from flask import current_app
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor

app = Flask(__name__)

@app.before_first_request
def init_db_pool():
    setup(app)
    
# @app.route('/')
# @app.route('/<name>')
# def hello(name=None):
#     return render_template('guest_form', name=name)

pool = None

def setup(app):
    global pool
    DATABASE_URL = os.environ['DATABASE_URL']
    app.logger.info("Creating DB connection pool")
    pool = ThreadedConnectionPool(1, 20, dsn=DATABASE_URL, sslmode='require')

@contextmanager
def get_db_connection():
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)

@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            yield cur
            if commit:
                conn.commit()
        finally:
            cur.close()

@app.route('/', methods = ["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        message = request.form["message"]

        with get_db_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO guestbook (name, message) VALUES (%s, %s);",
                (name, message),
            )
        return redirect("/") 

    with get_db_cursor() as cur:
        cur.execute("SELECT name, message FROM guestbook ORDER BY created_at DESC;")
        guests = cur.fetchall()

    return render_template("guest_form.html", guests=guests)
