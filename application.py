from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
import os
from cs50 import SQL
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQL("postgres://bcbfedessydwun:dbdc8f53173f93f71ff4b7c1ea51fefee2e4dac7d785d312c4f426eae16ce8ab@ec2-54-163-230-178.compute-1.amazonaws.com:5432/dat9s8lnbu4obk")

def login_required(f):
    """
    Borrowed from C$50 Finance
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["POST", "GET"])
@login_required
def index():
    return render_template("index.html")

@app.route("/error", methods=["GET"])
@login_required
def error():
    return render_template("error.html")

@app.route("/input", methods=["POST", "GET"])
@login_required
def input():
    return render_template("dataInput.html")

@app.route("/search", methods=["POST", "GET"])
@login_required
def search():
    return render_template("search.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return redirect("error.html", details="must provide username", errorcode='403')

        # Ensure password was submitted
        elif not request.form.get("password"):
            return redirect("error.html", details="must provide password", errorcode='403')
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return redirect("error.html", details="invalid username or password", errorcode='403')
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if not request.method == "POST":

        # User reached route via GET (as by clicking a link or via redirect)
        return render_template("register.html")

    else:

        # Ensure username was submitted
        if not request.form.get("username"):
            return redirect("error.html", details="must provide username", errorcode='400')
        # Ensure password was submitted
        elif not request.form.get("password"):
            return redirect("error.html", details="must provide password", errorcode='400')
        # Ensure confirmatory password was submitted
        elif not request.form.get("confirmation"):
            return redirect("error.html", details="must confirm password", errorcode='400')
        # Ensure passwords match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return redirect("error.html", details="passwords must match", errorcode='400')
        # Ensure username unique
        elif db.execute("SELECT username FROM users WHERE username = :name", name=request.form.get("username")):
            return redirect("error.html", details="username already taken", errorcode='400')

        # Registers new user to database, logs user in
        else:
            db.execute("INSERT INTO users (username, hash) VALUES(:username,:password)",
                       username=request.form.get("username"), password=generate_password_hash(request.form.get("password")))

            # Remember which user has logged in
            rows = db.execute("SELECT id FROM users WHERE username = :username",
                              username=request.form.get("username"))

            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")



@app.route("/logout", methods=["POST", "GET"])
def logout():
    return render_template("error.html")
