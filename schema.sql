-- Student Marketplace — database schema (SQLite)
-- Main process: register -> post listing -> search -> message seller -> mark as sold

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS favourites;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS listings;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id    TEXT    NOT NULL UNIQUE,          -- e.g. 24B031936
    full_name     TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE CHECK (email LIKE '%@%'),
    password_hash TEXT    NOT NULL,                 -- never store plain passwords
    phone         TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE
);

CREATE TABLE listings (
    listing_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id   INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    title       TEXT    NOT NULL,
    description TEXT,
    price       INTEGER NOT NULL CHECK (price >= 0),          -- tenge
    condition   TEXT    NOT NULL CHECK (condition IN ('new', 'used')),
    status      TEXT    NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'sold', 'hidden')),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE messages (
    message_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id  INTEGER NOT NULL REFERENCES listings(listing_id) ON DELETE CASCADE,
    sender_id   INTEGER NOT NULL REFERENCES users(user_id),
    receiver_id INTEGER NOT NULL REFERENCES users(user_id),
    text        TEXT    NOT NULL,
    sent_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (sender_id <> receiver_id)
);

CREATE TABLE favourites (
    favourite_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(user_id)       ON DELETE CASCADE,
    listing_id   INTEGER NOT NULL REFERENCES listings(listing_id) ON DELETE CASCADE,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, listing_id)      -- the same listing cannot be saved twice
);

-- Indexes for the most common searches
CREATE INDEX idx_listings_category_price ON listings(category_id, price);
CREATE INDEX idx_listings_status         ON listings(status);
CREATE INDEX idx_messages_listing        ON messages(listing_id);
CREATE INDEX idx_favourites_user          ON favourites(user_id);
