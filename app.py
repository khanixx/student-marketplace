"""Student Marketplace — prototype of the main user process.

register -> log in -> post listing -> search -> message seller -> mark as sold

Run:
    pip install flask
    python app.py          # creates marketplace.db on first start
    open http://127.0.0.1:5000

Test accounts (created by seed.sql): aruzhan@kbtu.kz, dias@kbtu.kz, ... password: password123
"""
import hmac
import os
import secrets
import sqlite3
from functools import wraps

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "marketplace.db")

app = Flask(__name__)
# Random key per run if SECRET_KEY is not set (sessions reset on restart, but the key is never guessable).
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,      # JS cannot read the session cookie
    SESSION_COOKIE_SAMESITE="Lax",     # cookie is not sent on cross-site POSTs (second CSRF barrier)
    CSRF_ENABLED=True,
)


# ---------- security: CSRF token + headers ----------

def csrf_token():
    """One random token per session; every POST form must send it back."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def csrf_field():
    return Markup('<input type="hidden" name="csrf_token" value="%s">') % csrf_token()


app.jinja_env.globals.update(csrf_token=csrf_token, csrf_field=csrf_field)


@app.before_request
def check_csrf():
    if request.method == "POST" and app.config["CSRF_ENABLED"]:
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not expected or not hmac.compare_digest(sent, expected):
            abort(400, "CSRF token missing or invalid.")


@app.after_request
def security_headers(resp):
    resp.headers["X-Frame-Options"] = "DENY"                       # no clickjacking via iframes
    resp.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp


# ---------- database helpers ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and test data. Seed users get the password 'password123'."""
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as f:
        db.executescript(f.read())
    with open(os.path.join(BASE_DIR, "seed.sql"), encoding="utf-8") as f:
        db.executescript(f.read())
    db.execute("UPDATE users SET password_hash = ?", (generate_password_hash("password123"),))
    db.commit()
    db.close()


def current_user():
    if "user_id" not in session:
        return None
    return get_db().execute("SELECT * FROM users WHERE user_id = ?", (session["user_id"],)).fetchone()


@app.context_processor
def inject_user():
    me = current_user()
    fav_ids = set()
    if me:
        fav_ids = {r[0] for r in get_db().execute(
            "SELECT listing_id FROM favourites WHERE user_id = ?", (me["user_id"],))}
    return {"me": me, "fav_ids": fav_ids}


def safe_next(url):
    """Only allow redirects to local paths (blocks //evil.com and /\\evil.com)."""
    if url and url.startswith("/") and not url.startswith(("//", "/\\")) and "\\" not in url:
        return url
    return url_for("index")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


# ---------- US-4: search ----------

@app.route("/")
def index():
    db = get_db()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    max_price = request.args.get("max_price", "").strip()

    sql = """SELECT l.*, c.name AS category, u.full_name AS seller
             FROM listings l
             JOIN categories c ON c.category_id = l.category_id
             JOIN users u ON u.user_id = l.seller_id
             WHERE l.status = 'active'"""
    params = []
    if q:
        sql += " AND (l.title LIKE ? OR l.description LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND l.category_id = ?"
        params.append(category)
    if max_price.isdigit():
        sql += " AND l.price <= ?"
        params.append(int(max_price))
    sql += " ORDER BY l.price"

    listings = db.execute(sql, params).fetchall()
    # categories with the number of active listings (shown on the filter chips)
    categories = db.execute(
        """SELECT c.*, COUNT(l.listing_id) AS n FROM categories c
           LEFT JOIN listings l ON l.category_id = c.category_id AND l.status = 'active'
           GROUP BY c.category_id ORDER BY c.name""").fetchall()
    grouped = not (q or category or max_price)   # home page = sections by category
    return render_template("index.html", listings=listings, categories=categories,
                           q=q, category=category, max_price=max_price, grouped=grouped)


# ---------- US-1, US-2: register / login / logout ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        student_id, name = f["student_id"].strip(), f["full_name"].strip()
        email, password = f["email"].strip().lower(), f["password"]
        if not (student_id and name and email and len(password) >= 6):
            flash("Fill in all fields. Password must be at least 6 characters.")
            return render_template("register.html")
        try:
            db = get_db()
            cur = db.execute(
                "INSERT INTO users (student_id, full_name, email, password_hash) VALUES (?, ?, ?, ?)",
                (student_id, name, email, generate_password_hash(password)))
            db.commit()
        except sqlite3.IntegrityError:
            flash("This student ID or email is already registered.")
            return render_template("register.html")
        session.clear()                     # new session after sign-up (also new CSRF token)
        session["user_id"] = cur.lastrowid
        flash("Welcome! Your account was created.")
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form["password"]):
            session.clear()
            session["user_id"] = user["user_id"]
            return redirect(safe_next(request.args.get("next")))   # no open redirect
        flash("Wrong email or password.")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])     # POST + CSRF: a link/img on another site cannot log you out
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------- US-3: post a listing ----------

@app.route("/listing/new", methods=["GET", "POST"])
@login_required
def new_listing():
    db = get_db()
    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    if request.method == "POST":
        f = request.form
        title, price = f["title"].strip(), f["price"].strip()
        if not title or not price.isdigit():
            flash("Title is required and price must be a whole number of tenge, 0 or more.")
            return render_template("new_listing.html", categories=categories)
        try:
            cur = db.execute(
                """INSERT INTO listings (seller_id, category_id, title, description, price, condition)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session["user_id"], f["category_id"], title, f["description"].strip(),
                 int(price), f["condition"]))
            db.commit()
        except sqlite3.IntegrityError:
            flash("Invalid category or condition.")
            return render_template("new_listing.html", categories=categories)
        flash("Listing published.")
        return redirect(url_for("listing", listing_id=cur.lastrowid))
    return render_template("new_listing.html", categories=categories)


# ---------- listing page + US-5 messages ----------

def get_listing(listing_id):
    row = get_db().execute(
        """SELECT l.*, c.name AS category, u.full_name AS seller, u.email AS seller_email
           FROM listings l JOIN categories c ON c.category_id = l.category_id
           JOIN users u ON u.user_id = l.seller_id WHERE l.listing_id = ?""",
        (listing_id,)).fetchone()
    if row is None:
        abort(404)
    return row


@app.route("/listing/<int:listing_id>", methods=["GET", "POST"])
def listing(listing_id):
    db = get_db()
    item = get_listing(listing_id)
    uid = session.get("user_id")

    if request.method == "POST":
        if not uid:
            return redirect(url_for("login", next=request.path))
        text = request.form["text"].strip()
        # buyer writes to the seller; seller replies to the chosen buyer
        if uid != item["seller_id"]:
            receiver = item["seller_id"]                     # buyer writes to the seller
        else:
            # seller may reply only to a buyer who already wrote about THIS listing
            rid = request.form.get("receiver_id", "")
            receiver = int(rid) if rid.isdigit() else 0
            if not db.execute("SELECT 1 FROM messages WHERE listing_id = ? AND sender_id = ?",
                              (listing_id, receiver)).fetchone():
                receiver = 0
        if text and receiver and receiver != uid:
            db.execute("INSERT INTO messages (listing_id, sender_id, receiver_id, text) VALUES (?, ?, ?, ?)",
                       (listing_id, uid, receiver, text))
            db.commit()
        return redirect(url_for("listing", listing_id=listing_id))

    messages, buyers = [], []
    if uid:
        # each user sees only conversations they take part in
        messages = db.execute(
            """SELECT m.*, s.full_name AS sender FROM messages m JOIN users s ON s.user_id = m.sender_id
               WHERE m.listing_id = ? AND (m.sender_id = ? OR m.receiver_id = ?)
               ORDER BY m.sent_at, m.message_id""", (listing_id, uid, uid)).fetchall()
        if uid == item["seller_id"]:
            buyers = db.execute(
                """SELECT DISTINCT u.user_id, u.full_name FROM messages m JOIN users u ON u.user_id = m.sender_id
                   WHERE m.listing_id = ? AND m.sender_id <> ?""", (listing_id, uid)).fetchall()
    return render_template("listing.html", item=item, messages=messages, buyers=buyers)


# ---------- US-6: mark as sold (owner only) ----------

@app.route("/listing/<int:listing_id>/sold", methods=["POST"])
@login_required
def mark_sold(listing_id):
    item = get_listing(listing_id)
    if item["seller_id"] != session["user_id"]:
        abort(403)  # only the owner may change the listing
    db = get_db()
    db.execute("UPDATE listings SET status = 'sold' WHERE listing_id = ?", (listing_id,))
    db.commit()
    flash("Marked as sold. It no longer appears in search.")
    return redirect(url_for("listing", listing_id=listing_id))


# ---------- US-7: my listings ----------

@app.route("/my")
@login_required
def my_listings():
    rows = get_db().execute(
        """SELECT l.*, c.name AS category FROM listings l JOIN categories c ON c.category_id = l.category_id
           WHERE l.seller_id = ? ORDER BY l.created_at DESC""", (session["user_id"],)).fetchall()
    return render_template("my_listings.html", listings=rows)


# ---------- favourites ----------

@app.route("/listing/<int:listing_id>/favourite", methods=["POST"])
def toggle_favourite(listing_id):
    back = safe_next(request.form.get("next"))
    if "user_id" not in session:
        flash("Please log in to save listings.")
        return redirect(url_for("login", next=back))
    get_listing(listing_id)  # 404 if it does not exist
    db = get_db()
    removed = db.execute("DELETE FROM favourites WHERE user_id = ? AND listing_id = ?",
                         (session["user_id"], listing_id)).rowcount
    if not removed:
        db.execute("INSERT INTO favourites (user_id, listing_id) VALUES (?, ?)",
                   (session["user_id"], listing_id))
    db.commit()
    return redirect(back)


@app.route("/favourites")
@login_required
def favourites():
    rows = get_db().execute(
        """SELECT l.*, c.name AS category, u.full_name AS seller
           FROM favourites f JOIN listings l ON l.listing_id = f.listing_id
           JOIN categories c ON c.category_id = l.category_id
           JOIN users u ON u.user_id = l.seller_id
           WHERE f.user_id = ? AND l.status <> 'hidden'
           ORDER BY f.favourite_id DESC""", (session["user_id"],)).fetchall()
    return render_template("favourites.html", listings=rows)


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    # debug mode only when asked for explicitly: the Werkzeug debugger allows running code
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
