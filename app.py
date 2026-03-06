from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)

DATABASE = "emergency.db"


# -----------------------
# DATABASE CONNECTION
# -----------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emergencies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            latitude REAL,
            longitude REAL,
            status TEXT DEFAULT 'Pending',
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_db()


# -----------------------
# HOME (CITIZEN SOS PAGE)
# -----------------------

@app.route("/")
def home():
    return render_template("citizen/home.html")


# -----------------------
# SOS API
# -----------------------

@app.route("/sos", methods=["POST"])
def sos():

    data = request.json

    emergency_type = data["type"]
    lat = data["latitude"]
    lon = data["longitude"]

    conn = get_db()

    conn.execute(
        "INSERT INTO emergencies(type, latitude, longitude) VALUES (?, ?, ?)",
        (emergency_type, lat, lon)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# -----------------------
# AUTHORITY LOGIN
# -----------------------

@app.route("/authority/login")
def authority_login():
    return render_template("authority/login.html")


# -----------------------
# AUTHORITY DASHBOARD
# -----------------------

@app.route("/authority/dashboard")
def authority_dashboard():

    conn = get_db()

    emergencies = conn.execute(
        "SELECT * FROM emergencies ORDER BY time DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "authority/dashboard.html",
        emergencies=emergencies
    )


# -----------------------
# POLICE LOGIN
# -----------------------

@app.route("/police/login")
def police_login():
    return render_template("authority/login.html")


# -----------------------
# POLICE DASHBOARD
# -----------------------

@app.route("/police/dashboard")
def police_dashboard():

    conn = get_db()

    emergencies = conn.execute(
        "SELECT * FROM emergencies WHERE type='crime'"
    ).fetchall()

    conn.close()

    return render_template(
        "authority/dashboard.html",
        emergencies=emergencies
    )


# -----------------------
# MEDICAL DASHBOARD
# -----------------------

@app.route("/medical/dashboard")
def medical_dashboard():

    conn = get_db()

    emergencies = conn.execute(
        "SELECT * FROM emergencies WHERE type='medical'"
    ).fetchall()

    conn.close()

    return render_template(
        "authority/dashboard.html",
        emergencies=emergencies
    )


# -----------------------
# FIRE DASHBOARD
# -----------------------

@app.route("/fire/dashboard")
def fire_dashboard():

    conn = get_db()

    emergencies = conn.execute(
        "SELECT * FROM emergencies WHERE type='fire'"
    ).fetchall()

    conn.close()

    return render_template(
        "authority/dashboard.html",
        emergencies=emergencies
    )


# -----------------------
# STATUS UPDATE
# -----------------------

@app.route("/update_status/<int:id>/<status>")
def update_status(id, status):

    conn = get_db()

    conn.execute(
        "UPDATE emergencies SET status=? WHERE id=?",
        (status, id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("authority_dashboard"))


# -----------------------
# RUN SERVER
# -----------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)