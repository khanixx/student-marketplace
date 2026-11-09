"""Automated tests for the main user process.  Run:  python -m pytest -v
Each test = one test case (TC) from the Status Check Pack."""
import os
import tempfile

import pytest

import app as marketplace


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    marketplace.DB_PATH = path
    marketplace.init_db()
    marketplace.app.config["TESTING"] = True
    marketplace.app.config["CSRF_ENABLED"] = False   # TC-01..16 test business logic; CSRF has its own tests below
    with marketplace.app.test_client() as c:
        yield c
    os.remove(path)


def register(c, sid="24B999001", email="new@kbtu.kz", password="secret1"):
    return c.post("/register", data={"student_id": sid, "full_name": "New Student",
                                     "email": email, "password": password}, follow_redirects=True)


def login(c, email="aruzhan@kbtu.kz", password="password123"):
    return c.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def test_tc01_register_success(client):
    r = register(client)
    assert b"Your account was created" in r.data


def test_tc02_register_duplicate_student_id(client):
    r = register(client, sid="24B000101", email="other@kbtu.kz")  # 24B000101 already exists
    assert b"already registered" in r.data


def test_tc03_password_is_hashed(client):
    register(client, password="secret1")
    import sqlite3
    db = sqlite3.connect(marketplace.DB_PATH)
    stored = db.execute("SELECT password_hash FROM users WHERE email='new@kbtu.kz'").fetchone()[0]
    assert stored != "secret1" and stored.startswith(("scrypt:", "pbkdf2:"))


def test_tc04_login_wrong_password(client):
    r = login(client, password="wrong")
    assert b"Wrong email or password" in r.data


def test_tc05_post_listing(client):
    login(client)
    r = client.post("/listing/new", data={"title": "Algorithms book", "category_id": "1", "price": "3000",
                                          "condition": "used", "description": "CLRS"}, follow_redirects=True)
    assert b"Listing published" in r.data and b"Algorithms book" in r.data


def test_tc06_negative_price_rejected(client):
    login(client)
    r = client.post("/listing/new", data={"title": "Bad", "category_id": "1", "price": "-5",
                                          "condition": "used", "description": ""}, follow_redirects=True)
    assert b"price must be" in r.data


def test_tc07_search_category_and_price(client):
    r = client.get("/?category=1&max_price=4000")  # Books up to 4000
    assert b"Discrete Math lecture notes" in r.data    # 2000
    assert b"Calculus textbook" not in r.data           # 4500, too expensive
    assert b"Mechanical keyboard" not in r.data         # other category


def test_tc08_send_message(client):
    login(client, email="madina@kbtu.kz")
    client.post("/listing/1", data={"text": "Can I see it today?"})
    r = client.get("/listing/1")
    assert b"Can I see it today?" in r.data


def test_tc09_mark_sold_hides_from_search(client):
    login(client)  # aruzhan owns listing 1
    client.post("/listing/1/sold")
    r = client.get("/?q=Calculus")
    assert b"Calculus textbook" not in r.data


def test_tc10_cannot_mark_others_listing(client):
    login(client, email="dias@kbtu.kz")  # listing 1 belongs to aruzhan
    r = client.post("/listing/1/sold")
    assert r.status_code == 403


def test_tc11_post_requires_login(client):
    r = client.get("/listing/new")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_tc12_favourite_toggle(client):
    login(client)  # aruzhan has listings 3 and 5 saved in seed data
    client.post("/listing/8/favourite", data={"next": "/"})
    r = client.get("/favourites")
    assert b"Mechanical keyboard" in r.data and b"Logitech wireless mouse" in r.data
    client.post("/listing/8/favourite", data={"next": "/"})        # second click removes it
    assert b"Mechanical keyboard" not in client.get("/favourites").data


def test_tc13_favourite_requires_login(client):
    r = client.post("/listing/8/favourite", data={"next": "/"})
    assert r.status_code == 302 and "/login" in r.headers["Location"]
    assert client.get("/favourites").status_code == 302


def test_tc14_home_grouped_by_category(client):
    r = client.get("/")
    assert b"cat-head" in r.data and b"Dorm items" in r.data and b"Services" in r.data


def test_tc15_favourite_redirect_is_local_only(client):
    login(client)
    r = client.post("/listing/8/favourite", data={"next": "//evil.example.com"})
    assert r.status_code == 302 and "evil.example.com" not in r.headers["Location"]


def test_tc16_favourites_are_private_per_user(client):
    login(client, email="dias@kbtu.kz")  # seed: dias saved only listing 3 (mouse); aruzhan also saved 5 (hoodie)
    r = client.get("/favourites")
    assert b"Logitech wireless mouse" in r.data and b"University hoodie" not in r.data


# ---------- security tests ----------

import re


@pytest.fixture
def csrf_client(client):
    marketplace.app.config["CSRF_ENABLED"] = True
    yield client
    marketplace.app.config["CSRF_ENABLED"] = False


def token_from(c, path):
    return re.search(rb'name="csrf_token" value="([^"]+)"', c.get(path).data).group(1).decode()


def test_tc17_post_without_csrf_token_rejected(csrf_client):
    r = csrf_client.post("/login", data={"email": "aruzhan@kbtu.kz", "password": "password123"})
    assert r.status_code == 400


def test_tc18_post_with_csrf_token_works(csrf_client):
    t = token_from(csrf_client, "/login")
    r = csrf_client.post("/login", data={"email": "aruzhan@kbtu.kz", "password": "password123",
                                         "csrf_token": t})
    assert r.status_code == 302
    t = token_from(csrf_client, "/listing/1")
    assert csrf_client.post("/listing/1/sold", data={}).status_code == 400          # forged request
    assert csrf_client.post("/listing/1/sold", data={"csrf_token": t}).status_code == 302


def test_tc19_login_next_is_local_only(client):
    for bad in ("https://evil.example.com", "//evil.example.com", "/\\evil.example.com"):
        r = client.post("/login?next=" + bad, data={"email": "aruzhan@kbtu.kz", "password": "password123"})
        assert r.status_code == 302 and "evil.example.com" not in r.headers["Location"]


def test_tc20_logout_requires_post(client):
    login(client)
    assert client.get("/logout").status_code == 405
    client.post("/logout")
    assert client.get("/my").status_code == 302          # logged out


def test_tc21_seller_can_reply_only_to_buyers(client):
    login(client)  # aruzhan owns listing 1
    client.post("/listing/1", data={"text": "spam", "receiver_id": "999"})
    client.post("/listing/1", data={"text": "x", "receiver_id": "abc"})   # used to crash with 500
    import sqlite3
    db = sqlite3.connect(marketplace.DB_PATH)
    assert db.execute("SELECT COUNT(*) FROM messages WHERE text IN ('spam', 'x')").fetchone()[0] == 0


def test_tc22_security_headers(client):
    r = client.get("/")
    assert r.headers["X-Frame-Options"] == "DENY" and r.headers["X-Content-Type-Options"] == "nosniff"
    assert "SameSite=Lax" in client.post("/login", data={"email": "aruzhan@kbtu.kz",
                                                          "password": "password123"}).headers["Set-Cookie"]
