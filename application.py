from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_session import Session
import os
from cs50 import SQL
from functools import wraps
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import matplotlib.pyplot as plt

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connects to PostgresSQL database
db = SQL("postgres://bcbfedessydwun:dbdc8f53173f93f71ff4b7c1ea51fefee2e4dac7d785d312c4f426eae16ce8ab@ec2-54-163-230-178.compute-1.amazonaws.com:5432/dat9s8lnbu4obk")

''' Organizes house residence approximations in a dict '''
# Estimated based on facebook.college.harvard.edu results

housePop = {
    "college": 6827,
    # House Totals
    "adams": 450,
    "cabot": 373,
    "currier": 367,
    "dudley": 121,
    "dunster": 394,
    "eliot": 441,
    "kirkland": 387,
    "leverett": 325,
    "lev_mckinlock": 180,
    "mather": 407,
    "pfoho": 400,
    "quincy": 483,
    "winthrop": 413,
    "nonswing_lowell": 19,
    # Swing Housing
    "fairfax": 56,
    "hampden": 61,
    "IH": 114,
    "ridgley": 41,

    # Freshman Dorm Totals
    "apley" : 29,
    "canaday" : 245,
    "grays" : 97,
    "greenough" : 86,
    "hollis" : 58,
    "holworthy" : 83,
    "hurlbut" : 58,
    "lionel" : 34,
    "masshall" : 14,
    "matthews" : 153,
    "mower" : 33,
    "pennypacker" : 104,
    "stoughton" : 58,
    "straus" : 96,
    "thayer" : 156,
    "weld" : 153,
    "wigg" :201,
}

# Adds/updates fields which are sums of those stored
# house totals
housePop['lowell'] = (housePop['nonswing_lowell'] + housePop['fairfax'] + housePop['hampden']
                      + housePop['IH'] + housePop['ridgley'])
housePop['leverett'] = housePop['leverett'] + housePop['lev_mckinlock']
# house groups
housePop['quad'] = housePop['pfoho'] + housePop['cabot'] + housePop['currier']
housePop['river'] = (housePop['adams'] + housePop ['dunster'] + housePop['eliot']
                     + housePop['kirkland'] + housePop['leverett'] + housePop['mather']
                     + housePop['quincy'] + housePop['winthrop'] + housePop['lowell'])
# freshman yards
housePop['elm_yard'] = housePop['grays'] + housePop['weld'] + housePop['matthews']
housePop['ivy_yard'] = (housePop['apley'] + housePop['hollis'] + housePop['holworthy']
                        + housePop['lionel'] + housePop['masshall'] + housePop['mower']
                        + housePop['stoughton'] + housePop['straus'])
housePop['crimson_yard'] = (housePop['greenough'] + housePop['wigg'] + housePop['hurlbut']
                            + housePop['pennypacker'])
housePop['oak_yard'] = housePop['canaday'] + housePop['thayer']


'''Defines flask routes'''

# Define login required decorator which ensures user is logged in for all app
# functions. Lifted from C$50 Finance Helpers
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

# Default route. Renders index.html, the homepage of the app
@app.route("/", methods=["POST", "GET"])
@login_required
def index():
    name = db.execute("SELECT name FROM users WHERE id=:identify", identify=session['user_id'])

    return render_template("index.html", name=name[0]['name'])

# Route which renders an image and can list details on user errors
@app.route("/error", methods=["GET"])
def error():
    return render_template("error.html")

# Route which handles user input of voter data
@app.route("/input", methods=["POST", "GET"])
@login_required
def input():
    # Selects campaign type to guide databae options
    campaignType = db.execute("SELECT account_type FROM users WHERE id=:identify", identify=session['user_id'])
    # Executes on GET requests or other methods of redirect
    if request.method != "POST":
        return render_template("dataInput.html", campaign=campaignType[0]['account_type'], success=False)
        # Success=False means an alert, telling the user that their input was recieved,
        # will not be triggered
    else:
        # Checks for required inputs

        if not request.form.get("firstname"):
            return render_template("error.html", details="must provide first name")

        if not request.form.get("lastname"):
            return render_template("error.html", details="must provide last name")

        # Gets username from user_id
        user = db.execute("SELECT username FROM users WHERE id = :identify", identify=session['user_id'])
        # Adds voter to database
        # Database structures vary for different types of campaign account
        if campaignType[0]['account_type'] == "registration":
            db.execute("INSERT INTO " + user[0]['username'] + " (firstname, lastname, house,"
                       "contact, entryway, state, hometown, registered, ballotrequest, "
                       "voted, email, phone)"
                       "VALUES (:firstname, :lastname, :house, :contact,"
                       ":entryway, :state, :hometown, :register, :ballot,"
                       ":voted, :email, :phone)",
                       firstname=request.form.get("firstname"), lastname=request.form.get("lastname"),
                       house=request.form.get("house"), entryway=request.form.get("entryway"),
                       contact=request.form.get("contact"), state=request.form.get("state"),
                       hometown=request.form.get("hometown"), register=request.form.get("register"),
                       ballot=request.form.get("ballot"), voted=request.form.get("voted"),
                       email=request.form.get("email"), phone=request.form.get("phone"))

        elif campaignType[0]['account_type'] == "house":
            db.execute("INSERT INTO " + user[0]['username'] + " (firstname, lastname,"
                       "contact, entryway, support, voted, email, phone)"
                       "VALUES (:firstname, :lastname, :contact, :entryway, :support,"
                       " :voted, :email, :phone)",
                       firstname=request.form.get("firstname"), lastname=request.form.get("lastname"),
                       entryway=request.form.get("entryway"),contact=request.form.get("contact"),
                       support=request.form.get("support"), voted=request.form.get("voted"),
                       email=request.form.get("email"), phone=request.form.get("phone"))

        else:
            db.execute("INSERT INTO " + user[0]['username'] + " (firstname, lastname, house,"
                       "entryway, contact, support, voted, email, phone)"
                       "VALUES (:firstname, :lastname, :house,"
                       ":entryway, :email, :phone)",
                       firstname=request.form.get("firstname"), lastname=request.form.get("lastname"),
                       house=request.form.get("house"), entryway=request.form.get("entryway"),
                       email=request.form.get("email"), phone=request.form.get("phone"))

        # Sends a JS alert to the user that the database process executed successfully.
        return render_template("dataInput.html", campaign=campaignType[0]['account_type'], success=True)

# Route allows the user to filter through their collected data, links to a form with
# which data can be updated
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
        # Exception to display houses for intra-house campaigns, in which house data is not collected
        # from each user to avoid redundancy.
        if campaignType == "house":
            dorm = db.execute("SELECT house FROM users WHERE id=:identify", identify=session['user_id'])
            return render_template("search.html", q=q, voters=voters, campaign=campaignType[0]['account_type'], house=dorm[0]['house'])

        else:
            return render_template("search.html", q=q, voters=voters, campaign=campaignType[0]['account_type'])

# Allows the user to update existing records
@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    # TODO
    voterid = request.form.get("voterid")
    return render_template("update.html", voterid=voterid)

# Renders pie charts to allow the user to get a ballpack image of progress
@app.route("/view", methods=["GET", "POST"])
@login_required
def view():
    """Use matplotlib to show pie charts of the state of progress
    https://matplotlib.org/examples/pie_and_polar_charts/pie_demo_features.html"""

    # Defaults to just displaying the form
    if request.method == "GET":
        return render_template("view", show=False)

    if request.method == "POST":
        district = request.form.get("district")

        # Gets database info
        user = db.execute("SELECT username FROM users WHERE id = :identify",
                          identify=session['user_id'])
        rows = db.execute("SELECT * FROM " + user[0]['username'] + "")

        # Draws a pie chart of voter reg information using matplotlib
        if session['campaign_type'] == "registration":

            registered = 0
            ballot_requsest = 0
            voted = 0
            contact = 0

            # Counts how many members of each category are present
            # Doesn't double count, assuming those who've completed later steps
            # have also done the pre-rec (to vote you have to be registered)
            for row in rows:
                if row['voted']:
                    voted += 1
                elif row['ballotrequest']:
                    ballot_request += 1
                elif row['registered']:
                    registered += 1
                elif row['contact']:
                    contact += 1

            no_contact = housePop['district'] - (registered + ballot_request + voted)

            # Pie chart, where the slices will be ordered and plotted counter-clockwise:
            labels = 'Registered', 'Ballot Requested', 'Voted', 'Contacted', 'Not Contacted'
            sizes = [registered // housePop['district'], ballot_request // housePop['district'],
                     voted // housePop['district'], contact // housePop['district'],
                     no_contact // housePop['district']]

            explode = (0, 0, 0.2, 0, 0)  # Causes the referenced slice ("voted") to pop out)

            fig1, ax1 = plt.subplots()
            ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                    shadow=True, startangle=90)
            ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

            plt.savefig('static/chart.png', bbox_inches='tight')
            return render_template("view.html", show=True)
        # Draws a pie chart of voter contact information using matplotlib
        else:

            support = 0
            lean_yes = 0
            undecided = 0
            lean_no = 0
            oppose = 0
            contact = 0

            # Counts how many members of each category are present
            # Doesn't double count, assuming those who've completed later steps
            # have also done the pre-rec (to vote you have to be registered)
            for row in rows:
                if row['support'] == 1:
                    support += 1
                elif row['support'] == 2:
                    lean_yes += 1
                elif row['support'] == 3:
                    undecided += 1
                elif row['support'] == 4:
                    lean_no += 1
                elif row['support'] == 5:
                    oppose += 1
                elif row['contact']:
                    contact += 1

            no_contact = housePop['district'] - (support + lean_yes + undecided
                         + lean_no + oppose + contact)

            # Pie chart, where the slices will be ordered and plotted counter-clockwise:
            labels = 'Support', 'Leaning Support', 'Undecided', 'Leaning Oppose', 'Oppose', 'Contacted', 'Not Contacted'
            sizes = [support // housePop['district'], lean_yes // housePop['district'],
                     undecided // housePop['district'], lean_no // housePop['district'],
                     oppose // housePop['district'], contact // housePop['district'],
                     no_contact // housePop['district']]

            explode = (0, 0, 0.2, 0, 0)  # Causes the referenced slice ("voted") to pop out)

            fig1, ax1 = plt.subplots()
            ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                    shadow=True, startangle=90)
            ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

            # Saves image to be displayed
            plt.savefig('static/chart.png', bbox_inches='tight')

            return render_template("view.html", show=True)


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

        # Remember campaign type
        session["campaign_type"] = rows[0]["account_type"]

        # If house campaign, remember house
        if session["campaign_type"] == "house":
            session["house"] = rows[0]["house"].lower()
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
                db.execute("CREATE TABLE " + user + " ("
                           "VoterId int UNIQUE,"
                           "FirstName varchar(128),"
                           "LastName varchar(128),"
                           "Entryway varchar(64),"
                           "Contact boolean,"
                           "Support smallint,"
                           "Email varchar(255),"
                           "Voted boolean,"
                           "Phone varchar(20))")

            else:
                db.execute("CREATE TABLE " + user + " ("
                           "VoterId int UNIQUE,"
                           "FirstName varchar(128),"
                           "LastName varchar(128),"
                           "House varchar(64),"
                           "Entryway varchar(64),"
                           "Support smallint,"
                           "Contact boolean,"
                           "Voted boolean,"
                           "Email varchar(255),"
                           "Phone varchar(20))")

            # Sets up autoincrement

            db.execute("CREATE SEQUENCE " + user + "_voterid_seq START WITH 1 INCREMENT BY 1;")

            db.execute("ALTER TABLE " + user + " "
            "ALTER voterid TYPE integer,"
            "ALTER voterid SET DEFAULT nextval('" + user + "_voterid_seq'),"
            "ALTER voterid SET NOT NULL;")

            # Remember which user has logged in
            rows = db.execute("SELECT * FROM users WHERE username = :username",
                              username=user)

            session["user_id"] = rows[0]["id"]

            # Remember campaign type
            session["campaign_type"] = rows[0]["account_type"]

            # If house campaign, remember house
            if session["campaign_type"] == "house":
                session["house"] = rows[0]["house"].lower()

            # Redirect user to home page
            return redirect("/")


@app.route("/logout", methods=["POST", "GET"])
def logout():
    # Forget any user_id
    session.clear()

    return redirect("/")
