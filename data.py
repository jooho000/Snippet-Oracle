"""
Defines the application's databases.
"""

import itertools
import random
import sqlite3
import sqlite_vec
import os
import uuid  # For generating unique shareable links
import mock_data

_desc_transformer = None


def _get_transformer():
    from sentence_transformers import SentenceTransformer

    global _desc_transformer
    if _desc_transformer is None:
        _desc_transformer = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    return _desc_transformer


# Create database file and connect to it
if not os.path.exists("databases"):
    os.mkdir("databases")
_db_path = os.path.join("databases", "snippet_oracle.db")

_db = sqlite3.connect(_db_path, check_same_thread=False)
_db.enable_load_extension(True)
sqlite_vec.load(_db)
_db.enable_load_extension(False)


def _init_db():
    """Initialize the database's tables."""
    cur = _db.cursor()

    # Create tables
    cur.executescript(
        """
        BEGIN;
        CREATE TABLE IF NOT EXISTS User (
            ID INTEGER PRIMARY KEY,
            Name TEXT UNIQUE,
            PasswordHash TEXT,
            ProfilePicture TEXT,    -- For storing profile picture URLs/paths
            Bio TEXT,               -- User biography
            Description VARCHAR(250)
        );
        CREATE TABLE IF NOT EXISTS Snippet (
            ID INTEGER PRIMARY KEY,
            Name TEXT,
            Code TEXT,
            Description TEXT,
            UserID INTEGER,
            ParentSnippetID INTEGER,
            Date,
            IsPublic BOOLEAN DEFAULT 0,
            ShareableLink TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS TagUse (
            SnippetID INTEGER,
            TagName TEXT,
            PRIMARY KEY (SnippetID, TagName),
            FOREIGN KEY (SnippetID) REFERENCES Snippet(SnippetID)
        );
        CREATE TABLE IF NOT EXISTS Links (
            ID INTEGER PRIMARY KEY,
            UserID INTEGER,
            Platform TEXT,  -- e.g., "GitHub", "Discord"
            URL TEXT,       -- The actual link
            FOREIGN KEY (UserID) REFERENCES User(ID)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS SnippetEmbedding USING vec0(
            SnippetID INTEGER PRIMARY KEY,
            Embedding float[384]
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
        DROP TABLE IF EXISTS SnippetEmbedding;
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


def create_snippet(name, code, user_id, description=None, tags=None, is_public=False):
    """Creates a new snippet, returning its integer ID."""
    cur = _db.cursor()

    shareable_link = str(uuid.uuid4())  # Generate unique link

    # Create the snippet
    cur.execute(
        """
        INSERT INTO Snippet (Name, Code, Description, UserID, Date, IsPublic, ShareableLink)
        VALUES (?, ?, ?, ?, datetime('now'), ?, ?)
        """,
        [name, code, description or "", user_id, int(is_public), shareable_link],
    )
    snippet_id = cur.lastrowid

    # Add its entries to the tag table
    if tags:
        cur.executemany(
            """
            INSERT INTO TagUse (SnippetID, TagName)
            VALUES (?, ?)
            """,
            [(snippet_id, tag) for tag in tags],
        )

    # Create a "summary" of the snippet description for smart search
    if description:
        embedding = _get_transformer().encode(description)
        cur.execute(
            "INSERT INTO SnippetEmbedding(SnippetID, Embedding) VALUES (?, ?)",
            [snippet_id, embedding],
        )

    _db.commit()
    return snippet_id


def get_snippet(snippet_id, user_id=None):
    cur = _db.cursor()

    if user_id:
        cur.execute("SELECT * FROM Snippet WHERE ID = ? AND (UserID = ? OR IsPublic = 1)", (snippet_id, user_id))
    else:
        cur.execute("SELECT * FROM Snippet WHERE ID = ? AND IsPublic = 1", (snippet_id,))

    snippet = cur.fetchone()
    
    if snippet:  # Ensure snippet is not None
        return {
            "id": snippet[0],
            "name": snippet[1],
            "code": snippet[2],
            "description": snippet[3],
            "user_id": snippet[4],
            "date": snippet[6],
            "is_public": bool(snippet[7]),  # Explicit conversion
            "shareable_link": snippet[8]
        }

    return None


def get_user_snippets(user_id):
    """
    Gets all snippets posted by a specific user.

    - "id": The integer ID of the snippet.
    - "name": The name of the snippet.
    - "code": The content of the snippet.
    - "description": The user-provided description.
    - "user_id": The author's integer ID.
    - "parent_snippet_id": The integer ID of the parent snippet or `None`.
    - "date": The date and time of this snippet's creation.
    """
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
            Date,
            IsPublic
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
            "is_public": snippet[7],
            "tags": get_tags_for_snippet(snippet[0])
        }
        for snippet in snippets
    ]


def set_snippet_visibility(snippet_id, is_public):
    """
    Set a snippet's visibility and removes shareable link if it becomes public
    """
    
    cur = _db.cursor()
    cur.execute(
        """
        UPDATE Snippet
        SET IsPublic = ?
        WHERE ID = ?
        """,
        [is_public, snippet_id],
    )
    _db.commit()


def get_snippet_by_shareable_link(link):
    """
    Fetches snippet using its unique shareable link
    """

    cur = _db.cursor()
    cur.execute(
        "SELECT ID, Name, Code, Description, UserID, Date, IsPublic FROM Snippet WHERE ShareableLink = ?",
        [link],
    )
    snippet = cur.fetchone()
    if snippet:
        return {
            "id": snippet[0],
            "name": snippet[1],
            "code": snippet[2],
            "description": snippet[3],
            "user_id": snippet[4],
            "date": snippet[5],
            "is_public": bool(snippet[6]),
        }
    return None


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


def smart_search_snippets(query):
    """
    Leverages AI technology to return summaries of all snippets that kinda fit a query.
    Verbatim name matches are also returned.

    - "id": The integer ID of the snippet.
    - "name": The full name of the snippet.
    """
    query_embedding = _get_transformer().encode(query)
    query_terms = ["%" + term.strip() + "%" for term in query.split(" ")]

    # Find snippets that have all query terms in their names
    cur = _db.cursor()
    cur.execute(
        """
        SELECT ID, Name
        FROM Snippet
        WHERE ("""
        + " AND ".join(["Name LIKE ?"] * len(query_terms))
        + """)
        ORDER BY length(Name) ASC, Name
        LIMIT 50
        """,
        query_terms,
    )
    name_matches: list[dict] = cur.fetchall()

    # Search by description embedding
    cur.execute(
        """
        WITH DescMatches AS (
            SELECT SnippetID, distance
            FROM SnippetEmbedding
            WHERE Embedding MATCH ?
                AND k = 50
        )
        SELECT
            Snippet.ID,
            Snippet.Name
        FROM
            DescMatches,
            Snippet ON Snippet.ID = DescMatches.SnippetID
        """,
        [query_embedding],
    )
    desc_matches = cur.fetchall()

    return [
        {"id": res[0], "name": res[1]}
        for res in itertools.chain(name_matches, desc_matches)
    ]

# Finds the tags by snippetID
def get_tags_for_snippet(snippet_id):
    """
    Fetches all tags associated with a given snippet.
    """
    cur = _db.cursor()
    cur.execute(
        """
        SELECT TagName FROM TagUse WHERE SnippetID = ?
        """,
        [snippet_id],
    )
    tags = cur.fetchall()

    return [tag[0] for tag in tags]  # Convert tuple list to a simple list

