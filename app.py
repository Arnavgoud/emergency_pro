from functools import wraps
import os
import time

import psycopg
from psycopg.rows import dict_row
from flask import Flask, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Set it in Railway Variables and redeploy."
    )

VALID_SOS_TYPES = {"crime", "medical", "fire"}
ROLE_TO_ASSIGNMENT = {"police": "Police", "medical": "Medical", "fire": "Fire"}
TYPE_TO_ASSIGNMENT = {"crime": "Police", "medical": "Medical", "fire": "Fire"}
DB_INIT_DONE = False


def get_db_connection():
    return psycopg.connect(DATABASE_URL)


def get_cursor(conn, as_dict=False):
    if as_dict:
        return conn.cursor(row_factory=dict_row)
    return conn.cursor()


def init_db():
    conn = get_db_connection()
    try:
        cur = get_cursor(conn)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS emergencies (
                id SERIAL PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'Dispatched',
                assigned_to VARCHAR(50) NOT NULL DEFAULT 'Not Assigned',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute(
            "ALTER TABLE emergencies ADD COLUMN IF NOT EXISTS assigned_to VARCHAR(50) NOT NULL DEFAULT 'Not Assigned';"
        )
        cur.execute(
            "ALTER TABLE emergencies ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;"
        )
        # Safe conversion for older varchar coordinates to numeric.
        # Invalid values are normalized to 0 to prevent startup failure.
        cur.execute(
            """
            UPDATE emergencies
            SET latitude = '0'
            WHERE NOT (latitude::text ~ '^-?[0-9]+(\\.[0-9]+)?$');
            """
        )
        cur.execute(
            """
            UPDATE emergencies
            SET longitude = '0'
            WHERE NOT (longitude::text ~ '^-?[0-9]+(\\.[0-9]+)?$');
            """
        )
        cur.execute(
            "ALTER TABLE emergencies ALTER COLUMN latitude TYPE DOUBLE PRECISION USING latitude::DOUBLE PRECISION;"
        )
        cur.execute(
            "ALTER TABLE emergencies ALTER COLUMN longitude TYPE DOUBLE PRECISION USING longitude::DOUBLE PRECISION;"
        )
        cur.execute(
            """
            CREATE OR REPLACE FUNCTION update_emergency_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        cur.execute(
            """
            DROP TRIGGER IF EXISTS trg_update_emergency_timestamp ON emergencies;
            CREATE TRIGGER trg_update_emergency_timestamp
            BEFORE UPDATE ON emergencies
            FOR EACH ROW
            EXECUTE FUNCTION update_emergency_timestamp();
            """
        )
        _seed_user(cur, "admin", "admin123", "admin")
        _seed_user(cur, "police1", "police123", "police")
        _seed_user(cur, "medic1", "medical123", "medical")
        _seed_user(cur, "fire1", "fire123", "fire")
        conn.commit()
    finally:
        conn.close()


def init_db_with_retry():
    attempts = 8
    delay_seconds = 2
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            init_db()
            return
        except Exception as exc:
            last_error = exc
            if attempt == attempts:
                raise RuntimeError(f"Database initialization failed: {last_error}") from last_error
            time.sleep(delay_seconds)


def ensure_db_initialized():
    global DB_INIT_DONE
    if DB_INIT_DONE:
        return
    init_db_with_retry()
    DB_INIT_DONE = True


def _seed_user(cur, username, raw_password, role):
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        return
    cur.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
        (username, generate_password_hash(raw_password), role),
    )


def login_required(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/authority/login")
        return view_fn(*args, **kwargs)

    return wrapped


def authority_only(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        role = session.get("role")
        if role not in {"admin", "police", "medical", "fire"}:
            return redirect("/authority/login")
        return view_fn(*args, **kwargs)

    return wrapped


@app.route("/")
def home():
    # Keep citizen landing page available even if DB is temporarily unavailable.
    return render_template("citizen/home.html")


@app.route("/login")
def login_alias():
    return redirect("/authority/login")


@app.route("/send_sos", methods=["POST"])
def send_sos():
    try:
        ensure_db_initialized()
    except Exception:
        return jsonify({"success": False, "error": "Service temporarily unavailable"}), 503
    data = request.get_json(silent=True) or {}
    emergency_type = (data.get("type") or "").strip().lower()
    lat = data.get("lat")
    lon = data.get("lon")

    if emergency_type not in VALID_SOS_TYPES:
        return jsonify({"success": False, "error": "Invalid emergency type"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid coordinates"}), 400

    assigned_to = TYPE_TO_ASSIGNMENT[emergency_type]

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO emergencies (type, latitude, longitude, status, assigned_to)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (emergency_type, lat, lon, "Dispatched", assigned_to),
        )
        conn.commit()
        return jsonify({"success": True, "assigned_to": assigned_to})
    except Exception as exc:
        return jsonify({"success": False, "error": f"Database error: {exc}"}), 500
    finally:
        if "conn" in locals():
            conn.close()


@app.route("/authority/login", methods=["GET", "POST"])
def authority_login():
    if request.method == "GET":
        return render_template(
            "login.html",
            demo_credentials=[
                ("admin", "admin123"),
                ("police1", "police123"),
                ("medic1", "medical123"),
                ("fire1", "fire123"),
            ],
        )
    try:
        ensure_db_initialized()
    except Exception:
        return render_template(
            "login.html",
            error="Database is temporarily unavailable. Please try again.",
            demo_credentials=[
                ("admin", "admin123"),
                ("police1", "police123"),
                ("medic1", "medical123"),
                ("fire1", "fire123"),
            ],
        ), 503

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    conn = get_db_connection()
    try:
        cur = get_cursor(conn, as_dict=True)
        cur.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username=%s",
            (username,),
        )
        user = cur.fetchone()
    finally:
        conn.close()

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        return redirect("/authority/dashboard")

    return render_template(
        "login.html",
        error="Invalid credentials",
        demo_credentials=[
            ("admin", "admin123"),
            ("police1", "police123"),
            ("medic1", "medical123"),
            ("fire1", "fire123"),
        ],
    ), 401


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/authority/login")


@app.route("/authority/dashboard")
@login_required
@authority_only
def authority_dashboard():
    try:
        ensure_db_initialized()
    except Exception:
        return render_template(
            "login.html",
            error="Database is temporarily unavailable. Please try again.",
        ), 503
    role = session["role"]
    conn = get_db_connection()
    try:
        cur = get_cursor(conn, as_dict=True)
        if role == "admin":
            cur.execute("SELECT * FROM emergencies ORDER BY id DESC")
        else:
            assigned_to = ROLE_TO_ASSIGNMENT[role]
            cur.execute(
                "SELECT * FROM emergencies WHERE assigned_to=%s ORDER BY id DESC",
                (assigned_to,),
            )
        emergencies = cur.fetchall()
    finally:
        conn.close()

    total = len(emergencies)
    active = sum(1 for e in emergencies if e["status"] != "Resolved")
    resolved = sum(1 for e in emergencies if e["status"] == "Resolved")

    return render_template(
        "authority/dashboard.html",
        emergencies=emergencies,
        total=total,
        active=active,
        resolved=resolved,
        role=role,
    )


@app.route("/api/emergency_count")
@login_required
@authority_only
def emergency_count():
    try:
        ensure_db_initialized()
    except Exception:
        return jsonify({"count": 0}), 503
    role = session["role"]
    conn = get_db_connection()
    try:
        cur = get_cursor(conn)
        if role == "admin":
            cur.execute("SELECT COUNT(*) FROM emergencies")
        else:
            cur.execute(
                "SELECT COUNT(*) FROM emergencies WHERE assigned_to=%s",
                (ROLE_TO_ASSIGNMENT[role],),
            )
        count = cur.fetchone()[0]
    finally:
        conn.close()

    return jsonify({"count": count})


@app.route("/update_status/<int:emergency_id>/<action>")
@login_required
@authority_only
def update_status(emergency_id, action):
    try:
        ensure_db_initialized()
    except Exception:
        return redirect("/authority/dashboard")
    role = session["role"]
    admin_actions = {
        "AssignPolice": ("Dispatched", "Police"),
        "AssignMedical": ("Dispatched", "Medical"),
        "AssignFire": ("Dispatched", "Fire"),
    }
    responder_actions = {"Acknowledged": "Acknowledged", "Resolved": "Resolved"}

    conn = get_db_connection()
    try:
        cur = get_cursor(conn)
        if action in admin_actions and role == "admin":
            status, assigned_to = admin_actions[action]
            cur.execute(
                """
                UPDATE emergencies
                SET status=%s, assigned_to=%s
                WHERE id=%s
                """,
                (status, assigned_to, emergency_id),
            )
        elif action in responder_actions:
            # responders can only change incidents assigned to them
            if role == "admin":
                cur.execute(
                    "UPDATE emergencies SET status=%s WHERE id=%s",
                    (responder_actions[action], emergency_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE emergencies
                    SET status=%s
                    WHERE id=%s AND assigned_to=%s
                    """,
                    (responder_actions[action], emergency_id, ROLE_TO_ASSIGNMENT[role]),
                )
        conn.commit()
    finally:
        conn.close()

    return redirect("/authority/dashboard")


if __name__ == "__main__":
    app.run(debug=False)
