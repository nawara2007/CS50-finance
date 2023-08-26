import requests
import os

# import json
import json

from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    response = requests.get(f'https://api.iex.cloud/v1/data/core/quote/{symbol}?token={os.environ.get("API_KEY")}')
    data = json.loads(response.text)

    # Access the desired value
    try:
        price = data[0]['iexRealtimePrice']
        CompanyName = data[0]['companyName']
        return {
            "name": CompanyName,
            "price": float(price),
            "symbol": symbol
        }
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
