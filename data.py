"""
Defines the application's databases.
"""

from datetime import datetime, timezone
import random
import sqlite3
import os

import mock_data

# from sentence_transformers import SentenceTransformer
# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Create database file and connect to it
if not os.path.exists("databases"):
    os.mkdir("databases")
_db_path = os.path.join("databases", "snippet_oracle.db")
_db = sqlite3.connect(_db_path, check_same_thread=False)


def _init_db():
    """Initialize the database's tables."""
    cur = _db.cursor()

    # Create User table
    cur.executescript(
        """
        BEGIN;
        CREATE TABLE IF NOT EXISTS User (
            ID INTEGER PRIMARY KEY,
            Name TEXT UNIQUE,
            PasswordHash TEXT,
            Description VARCHAR(250)
        );
        CREATE TABLE IF NOT EXISTS Snippet (
            ID INTEGER PRIMARY KEY,
            Name TEXT,
            Code TEXT,
            Description TEXT,
            UserID INTEGER,
            ParentSnippetID INTEGER,
            Date
        );
        CREATE TABLE IF NOT EXISTS TagUse (
            SnippetID INTEGER,
            TagName TEXT,
            PRIMARY KEY (SnippetID, TagName),
            FOREIGN KEY (SnippetID) REFERENCES Snippet(SnippetID)
        );
        COMMIT;
        """
    )


_init_db()


## GENERAL ##


def reset():
    """Clears all tables in the database."""
    cur = _db.cursor()
    cur.executescript(
        """
        BEGIN;
        DROP TABLE IF EXISTS TagUse;
        DROP TABLE IF EXISTS Snippet;
        DROP TABLE IF EXISTS User;
        COMMIT;
        """
    )
    _init_db()


def populate():
    """Fills all tables with a bunch of fake data."""

    for _ in range(50):
        user_name = mock_data.username()
        create_user(user_name, "N/A")
        user_id = get_user_by_name(user_name)["id"]

        for _ in range(random.randint(0, 20)):
            create_snippet(
                name=mock_data.title(),
                code=mock_data.code(),
                user_id=user_id,
                description=mock_data.paragraph(),
                tags=mock_data.tags(),
            )


## USER INFO ###


def get_user_by_id(user_id):
    """
    Returns a dictionary of user data, or `None` if a user with the given ID does not exist.

    - "name": The user's name.
    - "password_hash": An argon2 hash of the user's password.
    """

    cur = _db.cursor()
    cur.execute(
        """
        SELECT Name, PasswordHash
        FROM User
        WHERE ID == ?
        """,
        [user_id],
    )

    res = cur.fetchone()

    if res is None:
        return None
    else:
        return {"name": res[0], "password_hash": res[1]}


def get_user_by_name(name):
    """
    Returns a dictionary of user data, or `None` if a user with the given name does not exist.

    - "id": The user's integer ID.
    - "name": The user's name.
    - "password_hash": An argon2 hash of the user's password.
    """

    cur = _db.cursor()
    cur.execute(
        """
        SELECT ID, Name, PasswordHash
        FROM User
        WHERE Name == ?
        """,
        [name],
    )

    res = cur.fetchone()

    if res is None:
        return None
    else:
        return {"id": int(res[0]), "name": res[1], "password_hash": res[2]}


def create_user(name, password_hash):
    """Creates a new user account. Returns `True` if the account was created, `False` otherwise."""

    cur = _db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO User(Name, PasswordHash)
            VALUES(?, ?)
            """,
            [name, password_hash],
        )
        _db.commit()
        return True
    except sqlite3.IntegrityError:
        # Raised when Name was not unique
        return False


## SNIPPETS ###


def create_snippet(name, code, user_id, description=None, tags=None):
    """Creates a new snippet, returning its integer ID."""
    cur = _db.cursor()

    # Create the snippet
    cur.execute(
        """
        INSERT INTO Snippet (Name, Code, Description, UserID, Date)
        VALUES (?, ?, ?, ?, datetime('now'))
        """,
        [name, code, description or "", user_id],
    )
    id = cur.lastrowid

    # Add its entries to the tag table
    if tags is not None:
        cur.executemany(
            """
            INSERT INTO TagUse (SnippetID, TagName)
            VALUES (?, ?)
            """,
            [(id, tag) for tag in tags],
        )

    _db.commit()
    return id


def get_snippet(id):
    """
    Gets a snippet by integer ID.

    - "name": The name of the snippet.
    - "code": The content of the snippet.
    - "description": The user-provided description.
    - "user_id": The author's integer ID.
    - "parent_snippet_id": The integer ID of the parent snippet or `None`.
    - "date": The date and time of this snippet's creation.
    """
    cur = _db.cursor()
    cur.execute(
        "SELECT Name, Code, Description, UserID, ParentSnippetID, Date FROM Snippet WHERE id = ?",
        [id],
    )
    snippet = cur.fetchone()
    if snippet is None:
        return None

    return {
        "name": snippet[0],
        "code": snippet[1],
        "description": snippet[2],
        "user_id": snippet[3],
        "parent_snippet_id": snippet[4],
        "date": snippet[5],
    }


def get_user_snippets(user_id):
    cur = _db.cursor()
    cur.execute(
        """
        SELECT
            ID,
            Name,
            Code,
            Description,
            UserID,
            ParentSnippetID,
            Date
        FROM Snippet
        WHERE UserID = ?
        ORDER BY Date DESC
        """,
        [user_id],
    )
    snippets = cur.fetchall()

    return [
        {
            "id": snippet[0],
            "name": snippet[1],
            "code": snippet[2],
            "description": snippet[3],
            "user_id": snippet[4],
            "parent_snippet_id": snippet[5],
            "date": snippet[6],
        }
        for snippet in snippets
    ]


def search_snippets(names=None, tags=None, desc=None):
    """
    Returns summaries of all snippets that include the given elements.

    - "id": The integer ID of the snippet.
    - "name": The full name of the snippet.
    """

    if type(names) == str:
        names = [names]
    if type(tags) == str:
        tags = [tags]
    if type(desc) == str:
        desc = [desc]

    queries = []
    params = []

    # Snippet name includes any of the given names
    if names is not None and len(names) > 0:
        name_match = "(" + " OR ".join(["Name LIKE ?"] * len(names)) + ")"
        queries.append("SELECT Name, ID FROM Snippet WHERE " + name_match)
        params.extend(["%" + name + "%" for name in names])

    # Snippet tags include all of the given tags
    if tags is not None and len(tags) > 0:
        tags_match = "(" + ",".join(["?"] * len(tags)) + ")"
        queries.append(
            """
            SELECT S.Name, S.ID
            FROM Snippet AS S, TagUse AS T
            WHERE S.ID = T.SnippetID
            AND T.Tagname IN 
            """
            + tags_match
        )
        params.extend(tags)

    # Snippet description includes any of the given description text
    if desc is not None and len(desc) > 0:
        desc_match = "(" + " OR ".join(["Description LIKE ?"] * len(desc)) + ")"
        queries.append("SELECT Name, ID FROM Snippet WHERE " + desc_match)
        params.extend(["%" + desc_term + "%" for desc_term in desc])

    # Intersect all of the above queries
    if len(queries) == 0:
        query = "SELECT Name, ID FROM Snippet"
    else:
        query = " INTERSECT ".join(queries)

    cur = _db.cursor()
    results = cur.execute(query, params)

    return [{"name": result[0], "id": result[1]} for result in results]
