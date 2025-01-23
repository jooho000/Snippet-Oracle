"""
Defines the application's databases.
"""

import sqlite3
import os

if not os.path.exists("databases"):
    os.mkdir("databases")
db = sqlite3.connect(os.path.join("databases", "snippet_oracle.db"), check_same_thread=False)

def init():
    cur = db.cursor()

    # Create User table
    res = cur.execute("SELECT name FROM sqlite_master WHERE name='User'")
    if res.fetchone() is None:
        cur.execute(
            """
            CREATE TABLE User (
                ID INTEGER PRIMARY KEY,
                Name TEXT UNIQUE,
                PasswordHash TEXT,
                ProfilePicture TEXT,    -- Profile: To store file path or URL for profile picture
                Bio TEXT                -- Profile: To store the user's bio
            );
            """
        )

    # Create Snippet table
    res = cur.execute("SELECT name FROM sqlite_master WHERE name='Snippet'")
    if res.fetchone() is None:
        cur.execute(
            """
            CREATE TABLE Snippet (
                ID INTEGER PRIMARY KEY,
                Name TEXT,
                Code TEXT,
                Description TEXT,
                UserID INTEGER,
                ParentSnippetID INTEGER,
                Date
            );
            """
        )

    # Create TagUse table
    res = cur.execute("SELECT name FROM sqlite_master WHERE name='TagUse'")
    if res.fetchone() is None:
        cur.execute(
            """
            CREATE TABLE TagUse (
                ID INTEGER PRIMARY KEY,
                SnippetID INTEGER,
                Tag TEXT
            );
            """
        )

    # Create Links Table to store personal user links (e.g. Github, X, Discord, etc.)
    res = cur.execute("SELECT name FROM sqlite_master WHERE name='Links'")
    if res.fetchone() is None:
        cur.execute(
            """
            CREATE TABLE Links (
                ID INTEGER PRIMARY KEY,
                UserID INTEGER,
                Platform TEXT,  -- e.g., "GitHub", "X", "Discord"
                URL TEXT        -- The actual link (e.g., "https://github.com/user")
            );
            """
        )

    db.commit()
