import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    stocks = db.execute("SELECT symbol,shares FROM stocks WHERE id = ?", user_id)
    cash = float(db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"])
    quote = []

    for i in range(len(stocks)):
        adder = lookup(stocks[i]["symbol"])
        adder["shares"] = stocks[i]["shares"]
        quote.append(adder)

    total = cash
    for i in quote:
        total += (i["price"] * i["shares"])

    return render_template("index.html", quote=quote, cash=cash, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    now = datetime.now()

    if request.method == "POST":
        quote = lookup(request.form.get("symbol"))
        
        if not request.form.get("symbol") or quote == None:
            return apology("Invalid symbol")
        elif not request.form.get("shares"):
            return apology("Enter shares")
        
        shares = float(request.form.get("shares"))
        if shares <= 0:
            return apology("Invalid number of shares")
        
        stocks_Price = quote["price"] * shares
        user_id = session["user_id"]
        cash = float(db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"])
        
        if stocks_Price <= cash:
            db.execute("UPDATE users SET cash = ? WHERE id = ?", (cash - stocks_Price), user_id)
            
            stock_row = db.execute("SELECT * FROM stocks WHERE id = ? AND symbol = ?", user_id, request.form.get("symbol"))

            if len(stock_row) == 0:
                db.execute("INSERT INTO stocks (id, symbol, shares) VALUES (?,?,?)", user_id, request.form.get("symbol"), shares)
            else:
                old_shares = int(db.execute("SELECT shares FROM stocks WHERE id = ? AND symbol = ?", user_id, request.form.get("symbol"))[0]["shares"])
                db.execute("UPDATE stocks SET shares = ? WHERE id = ? AND symbol = ?", (old_shares + shares), user_id, request.form.get("symbol"))

            db.execute("INSERT INTO history (id, transacted, symbol, shares, price) VALUES (?,?,?,?,?)", user_id, now, quote["symbol"], shares, quote["price"])
            
            return redirect("/")
        else:
            return apology("No enough money")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    history = db.execute("SELECT symbol,shares,price,transacted FROM history WHERE id = ?", user_id)

    return render_template("history.html", history=history)

@app.route("/addCash", methods=["GET", "POST"])
@login_required
def addCash():
    """Add cash into user wallet"""
    if request.method == "POST":
        
        now = datetime.now()
        if not request.form.get("cash"):
            return apology("Enter cash")
        user_id = session["user_id"]
        curr_cash = float(db.execute("Select cash FROM users WHERE id = ?", user_id)[0]["cash"])
        new_cash = curr_cash +  float(request.form.get("cash"))
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash,user_id)
        db.execute("INSERT INTO history (id, transacted, symbol, shares, price) VALUES (?,?,?,?,?)", user_id, now, "Added Cash", 0, float(request.form.get("cash")))

        return redirect("/")

    else:
        return render_template("cash.html")

    

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Show history of transactions"""
    if request.method == "POST":
        if not request.form.get("curr_password") or not request.form.get("new_password") or not request.form.get("confirm_password"):
            return apology("Please enter the passwords")
        
        if request.form.get("new_password") != request.form.get("confirm_password"):
            return apology("The passwords doesnot match")
        
        user_id = session["user_id"]
        curr_password = db.execute("Select hash FROM users WHERE id = ?", user_id)[0]["hash"]


        if check_password_hash(curr_password, request.form.get("curr_password")):
            if check_password_hash(curr_password, request.form.get("new_password")):
                return apology("It is already your password")
            
            db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(request.form.get("new_password")), user_id)

            return redirect("/")
        else:
            return apology("your current password is incorreect")

    else:
        return render_template("password.html")
    


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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
    if request.method == "POST":
        quote = lookup(request.form.get("symbol"))

        if quote == None:
            return apology("Invalid symbol", 403)
        else:
            return render_template("quoted.html", name=quote["name"], price=quote["price"], symbol=quote["symbol"])
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)
        
        elif not request.form.get("confirm_password") or request.form.get("password") != request.form.get("confirm_password"):
            return apology("The password does not match", 403)
        
        checker = db.execute("Select * FROM users WHERE username = ?", request.form.get("username"))

        if len(checker) == 0:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username") , generate_password_hash(request.form.get("password")))

            session["user_id"] = db.execute("Select id FROM users WHERE username = ?", request.form.get("username"))

            return redirect("/login")
        else:
            return apology("This user is already registered", 403)
        
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    now = datetime.now()
    user_id = session["user_id"]
    stocks = []
    Symbols = db.execute("SELECT symbol FROM stocks WHERE id = ?", user_id)
    for i in Symbols:
        stocks.append(i["symbol"]) 

    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Enter a symbol")
        elif not request.form.get("shares"):
            return apology("Enter no of sahres")
        
        if request.form.get("symbol") in stocks:
            sold_shares = int(request.form.get("shares"))
            old_shares = int(db.execute("SELECT shares FROM stocks WHERE id = ? AND symbol = ?", user_id,  request.form.get("symbol"))[0]["shares"])
            if sold_shares > old_shares or sold_shares <=0:
                return apology("No enough shares")
            
            cash = float(db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"])
            quote = lookup(request.form.get("symbol"))

            if old_shares == sold_shares:
                db.execute("UPDATE users SET cash = ? WHERE id = ?", (cash+(sold_shares * quote["price"])), user_id)
                db.execute("DELETE FROM stocks WHERE id = ? AND symbol = ?", user_id, quote["symbol"])
            else:

                db.execute("UPDATE users SET cash = ? WHERE id = ?", (cash+(sold_shares * quote["price"])), user_id)
                db.execute("UPDATE stocks SET shares = ? WHERE id = ? AND symbol = ?", (old_shares-sold_shares), user_id, quote["symbol"])
            
            db.execute("INSERT INTO history (id, transacted, symbol, shares, price) VALUES (?,?,?,?,?)", user_id, now, quote["symbol"], -sold_shares, quote["price"])

            return redirect("/")
        else:
            return apology("Invalid symbol")
    else:
        return render_template("sell.html", stocks=stocks)

app.run(host="0.0.0.0", port=8080, threaded=True)
