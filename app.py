from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.permanent_session_lifetime = timedelta(minutes=30)

DATABASE = "database.db"


# ---------------- DB CONNECTION ----------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INIT DATABASE ----------------
def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emergencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            latitude REAL,
            longitude REAL,
            status TEXT DEFAULT 'Pending',
            assigned_to TEXT DEFAULT 'Not Assigned',
            created_at TEXT,
            updated_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    users = [
        ("admin", "admin123", "admin"),
        ("police", "police123", "police"),
        ("medical", "medical123", "medical"),
        ("fire", "fire123", "fire"),
    ]

    for user in users:
        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                user
            )
        except:
            pass

    conn.commit()
    conn.close()


init_db()


# ---------------- CITIZEN ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        emergency_type = request.form["type"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()
        conn.execute(
            """INSERT INTO emergencies 
               (type, latitude, longitude, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (emergency_type, latitude, longitude, now, now)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("citizen/home.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session.permanent = True
            session["user"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("authority_dashboard"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- DASHBOARD ----------------
@app.route("/authority/dashboard")
def authority_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    role = session["role"]

    if role == "admin":
        emergencies = conn.execute(
            "SELECT * FROM emergencies ORDER BY id DESC"
        ).fetchall()
    else:
        department_mapping = {
            "police": "Police Department",
            "medical": "Medical Team",
            "fire": "Fire Department"
        }

        dept = department_mapping.get(role)

        emergencies = conn.execute(
            "SELECT * FROM emergencies WHERE assigned_to=? ORDER BY id DESC",
            (dept,)
        ).fetchall()

    total = len(emergencies)
    active = len([e for e in emergencies if e["status"] != "Resolved"])
    resolved = len([e for e in emergencies if e["status"] == "Resolved"])

    conn.close()

    return render_template(
        "authority/dashboard.html",
        emergencies=emergencies,
        total=total,
        active=active,
        resolved=resolved,
        role=role
    )


# ---------------- UPDATE STATUS ----------------
@app.route("/update_status/<int:id>/<string:new_status>")
def update_status(id, new_status):

    if "user" not in session:
        return redirect(url_for("login"))

    role = session["role"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()

    if role == "admin" and new_status.startswith("Assign"):
        department_mapping = {
            "AssignPolice": "Police Department",
            "AssignMedical": "Medical Team",
            "AssignFire": "Fire Department"
        }

        assigned_department = department_mapping.get(new_status)

        conn.execute(
            """UPDATE emergencies 
               SET assigned_to=?, status='Dispatched', updated_at=? 
               WHERE id=?""",
            (assigned_department, now, id)
        )
    else:
        conn.execute(
            """UPDATE emergencies 
               SET status=?, updated_at=? 
               WHERE id=?""",
            (new_status, now, id)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("authority_dashboard"))


# ---------------- ALERT API ----------------
@app.route("/api/emergency_count")
def emergency_count():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM emergencies").fetchone()[0]
    conn.close()
    return {"count": total}


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)