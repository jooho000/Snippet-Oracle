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

    #create Tag Table:
    res = cur.execute("SELECT name FROM sqlite_master WHERE name='Tags'")
    if res.fetchone() is None:
        cur.execute(
            """
            CREATE TABLE Tags (
                ID INTEGER PRIMARY KEY,
                TagName TEXT UNIQUE,
                Usage INTEGER
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
                TagID,
                PRIMARY KEY (SnippetID, TagID),
                FOREIGN KEY (SnippetID) REFERENCES Snippet(ID)
                FOREIGN KEY (TagID) REFERENCES Tags(ID)
            );
            """
        )

    db.commit()
