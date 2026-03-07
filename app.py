from flask import Flask, render_template, request, jsonify, redirect
import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/emergency"

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# create table automatically
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emergencies (
            id SERIAL PRIMARY KEY,
            type VARCHAR(50),
            latitude VARCHAR(50),
            longitude VARCHAR(50),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()


@app.route("/")
def home():
    return render_template("citizen/home.html")


@app.route("/send_sos", methods=["POST"])
def send_sos():

    data = request.json
    emergency_type = data.get("type")
    lat = data.get("lat")
    lon = data.get("lon")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO emergencies (type, latitude, longitude, status) VALUES (%s,%s,%s,%s)",
            (emergency_type, lat, lon, "Pending")
        )

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        print(e)
        return jsonify({"success": False})


@app.route("/authority/dashboard")
def authority_dashboard():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM emergencies ORDER BY id DESC")
    emergencies = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("authority/dashboard.html", emergencies=emergencies)


@app.route("/acknowledge/<int:id>")
def acknowledge(id):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE emergencies SET status='Acknowledged' WHERE id=%s",(id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/authority/dashboard")


@app.route("/resolve/<int:id>")
def resolve(id):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE emergencies SET status='Resolved' WHERE id=%s",(id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/authority/dashboard")


if __name__ == "__main__":
    app.run()
