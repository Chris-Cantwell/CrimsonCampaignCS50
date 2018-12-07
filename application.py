from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_session import Session
import os
from cs50 import SQL
from functools import wraps
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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
def error():
    return render_template("error.html")

@app.route("/input", methods=["POST", "GET"])
@login_required
def input():
    # Selects campaign type to guide databae options
    campaignType = db.execute("SELECT account_type FROM users WHERE id=:identify", identify=session['user_id'])

    if request.method != "POST":
        return render_template("dataInput.html", campaign=campaignType[0]['account_type'], success=False)

    else:
        # Checks for required inputs

        if not request.form.get("firstname"):
            return render_template("error.html", details="must provide first name")

        if not request.form.get("lastname"):
            return render_template("error.html", details="must provide last name")

        # Gets username from user_id
        user = db.execute("SELECT username FROM users WHERE id = :identify", identify=session['user_id'])
        # Adds voter to database
        if campaignType[0]['account_type'] == "registration":
            db.execute("INSERT INTO " + user[0]['username'] + " (firstname, lastname, house,"
                       "entryway, state, hometown, email, phone)"
                       "VALUES (:firstname, :lastname, :house,"
                       ":entryway, :state, :hometown, :email, :phone)",
                       firstname=request.form.get("firstname"), lastname=request.form.get("lastname"),
                       house=request.form.get("house"), entryway=request.form.get("entryway"),
                       state=request.form.get("state"), hometown=request.form.get("hometown"),
                       email=request.form.get("email"), phone=request.form.get("phone"))

        elif campaignType[0]['account_type'] == "house":
            db.execute("INSERT INTO " + user[0]['username'] + " (firstname, lastname, house,"
                       "entryway, state, hometown, email, phone)"
                       "VALUES (:firstname, :lastname,:entryway, :email, :phone)",
                       firstname=request.form.get("firstname"), lastname=request.form.get("lastname"),
                       entryway=request.form.get("entryway"),email=request.form.get("email"),
                       phone=request.form.get("phone"))

        else:
            db.execute("INSERT INTO " + user[0]['username'] + " (firstname, lastname, house,"
                       "entryway, email, phone)"
                       "VALUES (:firstname, :lastname, :house,"
                       ":entryway, :email, :phone)",
                       firstname=request.form.get("firstname"), lastname=request.form.get("lastname"),
                       house=request.form.get("house"), entryway=request.form.get("entryway"),
                       email=request.form.get("email"), phone=request.form.get("phone"))

        return render_template("dataInput.html", campaign=campaignType[0]['account_type'], success=True)


@app.route("/search", methods=["POST", "GET"])
@login_required
def search():
    if request.method != "POST":
        campaignType = db.execute("SELECT account_type FROM users WHERE id=:identify", identify=session['user_id'])
        return render_template("search.html", campaign=campaignType[0]['account_type'])

    else:
        # Gets input string from user
        q = str(request.form.get("q"))
        # Gets active user's username to point to their database
        user = db.execute("SELECT username FROM users WHERE id = :identify", identify=session['user_id'])
        # Gets a list of dicts of all stored voters
        allVoters = db.execute("SELECT * FROM " + user[0]['username'] + "")

        # Puts all instances of which contain search as a substring (non case-sensitive)
        # into a dict which is then formatted into the webpage using Jinja
        voters = []
        if q == '':
            voters = allVoters
        else:
            for voter in allVoters:
                if (q.lower() in voter['firstname'].lower()) or (q.lower() in voter['lastname'].lower()):
                    voters.append(voter)

        # Formats voter list as an HTML table, with varying parameters to match campaign type
        campaignType = db.execute("SELECT account_type FROM users WHERE id= :identify", identify=session['user_id'])

        if campaignType == "house":
            dorm = db.execute("SELECT house FROM users WHERE id=:identify", identify=session['user_id'])
            return render_template("search.html", q=q, voters=voters, campaign=campaignType[0]['account_type'], house=dorm[0]['house'])

        else:
            return render_template("search.html", q=q, voters=voters, campaign=campaignType[0]['account_type'])

@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    voterid = request.form.get("voterid")
    return render_template("update.html", voterid=voterid)

@app.route("/view")
@login_required
def view():
    return render_template("update.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", details="must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", details="must provide password")
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["pass_hash"], request.form.get("password")):
            return render_template("error.html", details="invalid username or password")
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
            return render_template("error.html", details="must provide username")
        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", details="must provide password")
        # Ensure confirmatory password was submitted
        elif not request.form.get("confirmation"):
            return render_template("error.html", details="must confirm password")
        # Ensure passwords match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return render_template("error.html", details="passwords must match")
        # Ensure username unique
        elif db.execute("SELECT username FROM users WHERE username = :name", name=request.form.get("username")):
            return render_template("error.html", details="username already taken")
        # Ensure name was submitted
        elif not request.form.get("name"):
            return render_template("error.html", details="must provide name")
        # Ensure dorm was submitted
        elif not request.form.get("house"):
                return render_template("error.html", details="must provide dorm/house")
        # Ensure campaign type password was submitted
        elif not request.form.get("campaign-type"):
            return render_template("error.html", details="must declare campaign type")
        # Ensure passwords match

        # Registers new user to database, logs user in
        else:
            # adds new user to database
            user = request.form.get("username")
            db.execute("INSERT INTO users (username, pass_hash, account_type, name, house) VALUES(:username,:password,:type,:name,:house)",
                       username=user, password=generate_password_hash(request.form.get("password")),
                       type=request.form.get("campaign-type"), name=request.form.get("name"), house=request.form.get("house"))

            # Creates a new table based on the campaign type
            if request.form.get('campaign-type') == 'registration':
                db.execute("CREATE TABLE " + user + " ("
                           "VoterId int UNIQUE,"
                           "FirstName varchar(128),"
                           "LastName varchar(128),"
                           "House varchar(64),"
                           "Entryway varchar(64),"
                           "Contact boolean,"
                           "State varchar(64),"
                           "Hometown varchar(128),"
                           "Registered boolean,"
                           "BallotRequest boolean,"
                           "Voted boolean,"
                           "Email varchar(255),"
                           "Phone varchar(20))")

            elif request.form.get("campaign-type") == "house":
                db.execute("CREATE TABLE :username ("
                           "VoterId int UNIQUE,"
                           "FirstName varchar(128),"
                           "LastName varchar(128),"
                           "Entryway varchar(64),"
                           "Contact boolean,"
                           "Support smallint,"
                           "Email varchar(255),"
                           "Voted boolean,"
                           "Phone varchar(20))", username=user)

            else:
                db.execute("CREATE TABLE :username ("
                           "VoterId int UNIQUE,"
                           "FirstName varchar(128),"
                           "LastName varchar(128),"
                           "House varchar(64),"
                           "Entryway varchar(64),"
                           "Support smallint,"
                           "Contact boolean,"
                           "Voted boolean,"
                           "Email varchar(255),"
                           "Phone varchar(20))", username=user)

            # Sets up autoincrement

            db.execute("CREATE SEQUENCE " + user + "_voterid_seq START WITH 1 INCREMENT BY 1;")

            db.execute("ALTER TABLE " + user + ""
            "ALTER 'voterid' TYPE integer,"
            "ALTER 'voterid' SET DEFAULT nextval('" + user + "l_voterid_seq'),"
            "ALTER 'voterid' SET NOT NULL;")

            # Remember which user has logged in
            rows = db.execute("SELECT id FROM users WHERE username = :username",
                              username=user)

            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")


@app.route("/logout", methods=["POST", "GET"])
def logout():
    # Forget any user_id
    session.clear()

    return redirect("/")
