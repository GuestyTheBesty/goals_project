import requests

from flask import redirect, session
from functools import wraps
from datetime import date
import ast


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def in_the_past(input_date):
    try: 
        y, m, d = input_date.split("-")
        formatted_date = date(int(y), int(m), int(d))
    except (TypeError, ValueError): return False
    if formatted_date < date.today(): return True

def today():
    return date.today()

def to_tuple(string):
    return ast.literal_eval(string)

def days_difference(a, b):
    y, m, d = a.split("-")
    minuend = date(int(y), int(m), int(d))
    y, m, d = b.split("-")
    subtrahend = date(int(y), int(m), int(d))
    return (minuend - subtrahend).days