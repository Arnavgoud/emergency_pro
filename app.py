from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

DATABASE = "emergency.db"


# ------------------------
# DATABASE CONNECTION
# ------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emergencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            latitude REAL,
            longitude REAL,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ------------------------
# HOME PAGE
# ------------------------

@app.route("/")
def home():
    return render_template("citizen/home.html")


# ------------------------
# SOS API
# ------------------------

@app.route("/sos", methods=["POST"])
def sos():

    data = request.get_json()

    emergency_type = data.get("type")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    conn = get_db()

    conn.execute(
        "INSERT INTO emergencies (type, latitude, longitude) VALUES (?, ?, ?)",
        (emergency_type, latitude, longitude)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ------------------------
# AUTHORITY DASHBOARD
# ------------------------

@app.route("/authority/dashboard")
def authority_dashboard():

    conn = get_db()

    emergencies = conn.execute(
        "SELECT * FROM emergencies ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template("authority/dashboard.html", emergencies=emergencies)


# ------------------------
# RUN SERVER
# ------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)