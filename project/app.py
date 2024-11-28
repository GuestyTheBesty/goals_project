from flask import Flask, redirect, render_template, request, session
from flask_session import Session
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

from autrefunctions import login_required, in_the_past, today, to_tuple, days_difference

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

con = sqlite3.connect("goals.db", check_same_thread=False)
cur = con.cursor()

cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY NOT NULL,
        username TEXT NOT NULL,
        hash_password TEXT NOT NULL,
        UNIQUE (username)
    )
''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY NOT NULL,
        user_id INTEGER  NOT NULL,
        type TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        goal_date DATE NOT NULL,
        date DATE NOT NULL,
        completed BOOL NOT NULL,
        completed_date DATE,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
''')
con.commit()

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form.get("c_password")
        new = request.form.get("n_password")
        confirm = request.form.get("confirmpassword")

        if not (current and new and confirm): return "Fill out all required fields"
        if new != confirm: return "Confirmation password doesn't match"

        id = session["user_id"]
        actual_current = cur.execute("SELECT hash_password FROM users WHERE id = ?", (id,)).fetchall()
        if not check_password_hash(actual_current[0][0], current): return "Incorrect current password"

        cur.execute("UPDATE users SET hash_password = ? WHERE id = ?", (generate_password_hash(new), id))
        return redirect("/")
    return render_template("change_password.html")

@app.route("/completed_goals", methods=["GET", "POST"])
@login_required
def completed_goals():
    if request.method == "POST":
        c_goal = to_tuple(request.form.get("goal"))
        days = days_difference(c_goal[5], c_goal[8])
        after_days = days_difference(c_goal[8], c_goal[5])

        return render_template("c_goal.html", c_goal=c_goal, days=days, after_days=after_days)
    c_goals = cur.execute("SELECT * FROM goals WHERE user_id = ? AND completed != 0 ORDER BY completed_date DESC", (session["user_id"],)).fetchall()
    if not c_goals: return render_template("nocompletegoals.html")

    return render_template("completed_goals.html", c_goals=c_goals)

@app.route("/create_goal", methods=["GET", "POST"])
@login_required
def create_goal():
    if request.method == "POST":
        type = request.form.get("goal_type")
        if type != "Long" and type != "Short": return "Type has to be either Long or Short"

        goal_name = request.form.get("goal_name")
        if len(goal_name) > 100: return "Too long of a goal name"

        description = request.form.get("goal_description")
        if len(description) > 1000: return "Too long of a goal description"

        goal_date = request.form.get("deadline_date")
        if in_the_past(goal_date): return "Something went wrong"
        
        if not (type and goal_name and goal_date and description): return "Fill out all fields"
        
        cur.execute("INSERT INTO goals (user_id, type, name, description, goal_date, date, completed) VALUES (?, ?, ?, ?, ?, ?, 0)", 
                    (session["user_id"], type, goal_name, description, goal_date, today()))
        con.commit()
        return redirect("/")
    return render_template("create_goal.html")

@app.route("/goal", methods=["POST"])
@login_required
def goal():
    goal = to_tuple(request.form.get("status"))

    if not goal[7]: cur.execute("UPDATE goals SET completed = 1, completed_date = ? WHERE id = ?", (today(), goal[0]))
    else: cur.execute("UPDATE goals SET completed = 0 WHERE id = ?", (goal[0],))
    
    con.commit()
    return redirect("/")

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        goal = to_tuple(request.form.get("goal"))
        time = days_difference(goal[5], str(today()))

        return render_template("goal.html", goal=goal, time=time, today=today())
    goals = cur.execute("SELECT * FROM goals WHERE user_id = ? AND completed = 0 ORDER BY goal_date", (session["user_id"],)).fetchall()
    if not goals: return render_template("nogoals.html")

    incomplete = []
    for goal in goals[:]:
        if in_the_past(goal[5]):
            incomplete.append(goal)
            goals.remove(goal)

    return render_template("index.html", goals=goals, incomplete=incomplete)

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username").rstrip()
        password = request.form.get("password")

        if not (username and password): return "Fill out all fields"
        check = cur.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()
        if not (check and check_password_hash(check[0][2], password)): return "Incorrect username or password"

        session["user_id"] = check[0][0]
        return redirect("/")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username").rstrip()
        password = request.form.get("password")
        confirmation = request.form.get("confirmpassword")

        if not (username and password and confirmation): return "Fill out all fields"
        if password != confirmation: return "Password does not match retyped password"

        try: cur.execute("INSERT INTO users (username, hash_password) VALUES (?, ?)", (username, generate_password_hash(password)))
        except sqlite3.IntegrityError: return "Username taken"

        con.commit()
        return redirect("/login")
    return render_template("signup.html")