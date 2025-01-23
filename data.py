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
                Description varchar(250)
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
                SnippetID INTEGER,
                TagName TEXT,
                PRIMARY KEY (SnippetID, TagName),
                FOREIGN KEY (SnippetID) REFERENCES Snippet(SnippetID)
            );
            """
        )

    db.commit()
