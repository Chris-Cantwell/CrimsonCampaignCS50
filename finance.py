import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Gets cash remaining in user's account
    cashData = db.execute("SELECT cash FROM users WHERE id = :user",
                          user=session['user_id'])

    cash = cashData[0]['cash']

    # Updates portfolio information
    portfolio_old = db.execute("SELECT symbol FROM portfolio WHERE id = :identify", identify=session['user_id'])

    for old_stock in portfolio_old:
        current_stock = lookup(old_stock['symbol'])
        db.execute("UPDATE portfolio SET price = :newprice WHERE symbol = :symbol", newprice=current_stock['price'],
                   symbol=old_stock['symbol'])

    # Retrieves complete and updated portfolio information
    portfolio = db.execute("SELECT name, symbol, number, price FROM portfolio WHERE id = :identify", identify=session['user_id'])
    total = cash

    stocks = list()

    if not portfolio:
        return render_template('index.html', stocks=stocks, cash=cash, total=total)

    else:
        stocks = list()
        # Creates a list of stock dictionaries to be displayed in the table
        for item in portfolio:
            stock = item
            stock['totalCost'] = item['number'] * item['price']
            stocks.append(stock)

        total = cash

        for stock in stocks:
            total += stock['totalCost']
            stock['totalCost'] = usd(stock['totalCost'])
            stock['price'] = usd(stock['price'])

        return render_template('index.html', stocks=stocks, cash=usd(cash), total=usd(total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # Renders webpage on a GET request or redirect
    if not request.method == "POST":
        return render_template('buy.html')

    else:
        # Checks for valid input
        if not request.form.get('symbol'):
            return apology('must provide symbol', 400)

        elif not request.form.get('shares'):
            return apology('must provide shares', 400)

        elif not int(request.form.get('shares')) or str(int(request.form.get('shares'))) != request.form.get('shares'):
            return apology('share requests must be integers', 400)

        elif int(request.form.get('shares')) < 0:
            return apology('share requests must be positive')

        stock = lookup(request.form.get('symbol'))

        if not stock:
            return apology('Invalid Symbol', 400)

        # Purchases stock if the user can afford it

        budget = db.execute("SELECT cash FROM users WHERE id = :user",
                            user=session['user_id'])

        numShares = int(request.form.get('shares'))

        if budget[0]['cash'] > ((stock['price']) * numShares):

            shares = db.execute("SELECT number FROM portfolio WHERE id = :user AND symbol = :share",
                                user=session['user_id'], share=request.form.get('symbol'))

            if not shares:
                # Adds to a new entry to the portfolio
                db.execute("INSERT INTO portfolio (id, name, symbol, price, number) VALUES(:identifier, :name, :symbol, :price, :number)",
                           identifier=session['user_id'], name=stock['name'], symbol=stock['symbol'], price=stock['price'], number=numShares)

            else:
                # Increases the number of an existing share in the portfolio
                db.execute("UPDATE portfolio SET number = number + :purchase WHERE id = :user AND symbol = :share",
                           purchase=numShares, user=session['user_id'], share=request.form.get('symbol'))

            db.execute("UPDATE users SET cash = cash - :cost WHERE id = :identifier",
                       cost=stock['price'] * numShares, identifier=session['user_id'])

            db.execute("INSERT INTO ledger (number, price, action, user_id, symbol) VALUES(:number, :price, 'BUY', :identify, :symbol)",
                       number=numShares, price=stock['price'], identify=session['user_id'], symbol=request.form.get('symbol'))

            return redirect("/")

        else:
            return apology('Not Enough Funds', 400)


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    username = request.args.get('username')

    if len(username) >= 1:
        # Checks if username already exists in the database
        test = execute.db("SELECT username FROM users WHERE username = :username", username=username)
        if not test:
            return jsonify(True)
        else:
            return jsonify(False)
    else:
        return jsonify(False)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # There's more table redundancy than I would like, but one updating table and one static one aren't gonna mesh
    ledger = db.execute("SELECT * FROM ledger WHERE user_id = :user", user=session['user_id'])

    for transaction in ledger:
        transaction['price'] = usd(transaction['price'])

    return render_template("history.html", ledger=ledger)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if not request.method == "POST":
        return render_template('quote.html')

    else:
        # Checks for valid input
        if not request.form.get('symbol'):
            return apology('must provide symbol', 400)

        stock = lookup(request.form.get('symbol'))

        if not stock:
            return apology('Invalid Symbol', 400)

        return render_template('quoted.html', name=stock['name'], symbol=stock['symbol'], price=usd(stock['price']))


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
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmatory password was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # Ensure passwords match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords must match", 400)

        # Ensure username unique
        elif db.execute("SELECT username FROM users WHERE username = :name", name=request.form.get("username")):
            return apology("username already taken", 400)

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


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Returns the webpage in the case of a GET request or redirect
    if not request.method == "POST":

        sharesDict = db.execute("SELECT symbol FROM portfolio WHERE id = :identify", identify=session['user_id'])

        # Converts dictionary into a list
        shares = list()

        for item in sharesDict:
            shares.append(item['symbol'])

        return render_template('sell.html', shares=shares)

    else:
        # Ensures valid input
        if not request.form.get('symbol'):
            return apology("Must select a share", 400)

        elif not request.form.get('shares'):
            return apology('Must specify number of shares', 400)

        symbol = request.form.get('symbol')
        inputNum = int(request.form.get('shares'))

        if inputNum < 0:
            return apology('must specify a positive integer')

        numShares = db.execute("SELECT number FROM portfolio WHERE id = :identify and symbol = :share",
                               identify=session['user_id'], share=symbol)

        if not numShares or numShares[0]['number'] < inputNum:
            return apology('Not enough shares to sell', 400)

        sharePriceDict = db.execute("SELECT price FROM portfolio WHERE id = :identify and symbol = :share ",
                                    identify=session['user_id'], share=symbol)

        sharePrice = sharePriceDict[0]['price']

        if numShares[0]['number'] > inputNum:
            # Removes specified shares from the user's portfolio
            db.execute("UPDATE portfolio SET number = number - :sold WHERE id = :identify AND symbol = :share",
                       sold=inputNum, identify=session['user_id'], share=symbol)

        else:
            # Deletes share from portfolio if num == 0
            db.execute("DELETE FROM portfolio WHERE id = :identify AND symbol = :share", identify=session['user_id'], share=symbol)

        # Credits user's account with profit from sold stock
        db.execute("UPDATE users SET cash = (cash + :profit) WHERE id = :identify",
                   profit=(inputNum * sharePrice), identify=session['user_id'])

        # Update ledger of transactions
        db.execute("INSERT INTO ledger (number, price, action, user_id, symbol) VALUES(:number, :price, 'SELL', :identify, :symbol)",
                   number=inputNum, price=sharePrice, identify=session['user_id'], symbol=symbol)

        # Redirect user to home page
        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
