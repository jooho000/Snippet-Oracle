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
            IsPublic BOOLEAN DEFAULT 0, --0 for private and 1 for public
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
        CREATE TABLE IF NOT EXISTS SnippetPermissions (
            SnippetID INTEGER,
            UserID INTEGER,
            PRIMARY KEY (SnippetID, UserID),
            FOREIGN KEY (SnippetID) REFERENCES Snippet(ID),
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


def create_snippet(name, code, user_id, description=None, tags=None, is_public=False, permitted_users=None):
    """Creates a new snippet, returning its integer ID."""
    cur = _db.cursor()

    shareable_link = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO Snippet (Name, Code, Description, UserID, Date, IsPublic, ShareableLink)
        VALUES (?, ?, ?, ?, datetime('now'), ?, ?)
        """,
        [name, code, description or "", user_id, int(is_public), shareable_link],
    )
    snippet_id = cur.lastrowid

    if not is_public and permitted_users:
        permitted_users = [int(uid) for uid in permitted_users if str(uid).isdigit()]
        for permitted_user_id in permitted_users:
            if permitted_user_id != user_id:  # Avoid duplicate entry for creator
                cur.execute(
                    """
                    INSERT OR IGNORE INTO SnippetPermissions (SnippetID, UserID)
                    VALUES (?, ?)
                    """,
                    [snippet_id, permitted_user_id],
                )

    if tags:
        cur.executemany(
            """
            INSERT INTO TagUse (SnippetID, TagName)
            VALUES (?, ?)
            """,
            [(snippet_id, tag) for tag in tags],
        )

    _db.commit()

    return snippet_id


def get_snippet(snippet_id, user_id=None):
    cur = _db.cursor()

    cur.execute(
        """
        SELECT * FROM Snippet 
        WHERE ID = ? 
        AND (IsPublic = 1 
             OR UserID = ? 
             OR EXISTS (
                 SELECT 1 FROM SnippetPermissions 
                 WHERE SnippetID = ? 
                 AND UserID = ?
             )
        )
        """,
        (snippet_id, user_id, snippet_id, user_id),
    )

    snippet = cur.fetchone()

    if snippet:
        return {
            "id": snippet[0],
            "name": snippet[1],
            "code": snippet[2],
            "description": snippet[3],
            "user_id": snippet[4],
            "date": snippet[6],
            "is_public": bool(snippet[7]),
            "shareable_link": snippet[8],
        }

    return None  # Snippet not found or not accessible


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
            "is_public": snippet[7]
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


def search_snippets(names=None, tags=None, desc=None, user_id=None):
    """
    Returns summaries of all snippets that include the given elements and that
    the user has permission to view.

    - "id": The integer ID of the snippet.
    - "tags": A list of tags associated with the snippet.
    - "name": The full name of the snippet.
    - "desc": The user-provided description.
    - "user_id": The author's integer ID.
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
    if names:
        name_match = "(" + " OR ".join(["S.Name LIKE ?"] * len(names)) + ")"
        queries.append(name_match)
        params.extend(["%" + name + "%" for name in names])

    # Snippet tags include all of the given tags
    if tags:
        tags_match = "(" + ",".join(["?"] * len(tags)) + ")"
        queries.append(
            f"""
            EXISTS (
                SELECT 1 FROM TagUse AS T
                WHERE S.ID = T.SnippetID
                AND T.TagName IN {tags_match}
            )
            """
        )
        params.extend(tags)

    # Snippet description includes any of the given description text
    if desc:
        desc_match = "(" + " OR ".join(["S.Description LIKE ?"] * len(desc)) + ")"
        queries.append(desc_match)
        params.extend(["%" + desc_term + "%" for desc_term in desc])

    # Ensure only accessible snippets are returned
    access_filter = """
        (S.IsPublic = 1 OR EXISTS (
            SELECT 1 FROM SnippetPermissions AS P
            WHERE P.SnippetID = S.ID AND P.UserID = ?
        ))
    """
    queries.append(access_filter)
    params.append(user_id)

    # Final query with filters applied
    query = f"""
        SELECT S.ID, S.Name
        FROM Snippet AS S
        WHERE {" AND ".join(queries)}
        ORDER BY S.Date DESC
    """

    cur = _db.cursor()
    results = cur.execute(query, params)

    return [{"id": result[0], "name": result[1]} for result in results]

def smart_search_snippets(query, user_id=None):
    """
    Leverages AI to return summaries of all snippets that match a query,
    but ensures only accessible snippets are returned.

    - "id": The integer ID of the snippet.
    - "name": The full name of the snippet.
    """
    query_embedding = _get_transformer().encode(query)
    query_terms = ["%" + term.strip() + "%" for term in query.split(" ")]

    cur = _db.cursor()

    # Find snippets that have all query terms in their names
    cur.execute(
        f"""
        SELECT ID, Name
        FROM Snippet
        WHERE ({" AND ".join(["Name LIKE ?"] * len(query_terms))})
        AND (IsPublic = 1 OR EXISTS (
            SELECT 1 FROM SnippetPermissions WHERE SnippetID = Snippet.ID AND UserID = ?
        ))
        ORDER BY length(Name) ASC, Name
        LIMIT 50
        """,
        query_terms + [user_id],
    )
    name_matches = cur.fetchall()

    # Search by description embedding
    cur.execute(
        f"""
        WITH DescMatches AS (
            SELECT SnippetID, distance
            FROM SnippetEmbedding
            WHERE Embedding MATCH ?
                AND k = 50
        )
        SELECT
            Snippet.ID,
            Snippet.Name
        FROM DescMatches
        JOIN Snippet ON Snippet.ID = DescMatches.SnippetID
        WHERE (Snippet.IsPublic = 1 OR EXISTS (
            SELECT 1 FROM SnippetPermissions WHERE SnippetID = Snippet.ID AND UserID = ?
        ))
        """,
        [query_embedding, user_id],
    )
    desc_matches = cur.fetchall()

    return [
        {"id": res[0], "name": res[1]}
        for res in itertools.chain(name_matches, desc_matches)
    ]

def grant_snippet_permission(snippet_id, user_id):
    """
    Grants a user permission to view a snippet.
    
    Returns True if permission was granted, False if it already exists.
    """
    cur = _db.cursor()
    try:
        cur.execute(
            """
            INSERT INTO SnippetPermissions (SnippetID, UserID)
            VALUES (?, ?)
            """,
            [snippet_id, user_id],
        )
        _db.commit()
        return True
    except sqlite3.IntegrityError:
        # Permission already exists
        return False

def revoke_snippet_permission(snippet_id, user_id):
    """
    Revokes a user's permission to view a snippet.
    
    Returns True if permission was revoked, False if the permission did not exist.
    """
    cur = _db.cursor()
    cur.execute(
        """
        DELETE FROM SnippetPermissions
        WHERE SnippetID = ? AND UserID = ?
        """,
        [snippet_id, user_id],
    )
    if cur.rowcount > 0:
        _db.commit()
        return True
    return False

def user_has_permission(snippet_id, user_id):
    """
    Checks if a user has permission to view a snippet.
    
    Returns True if the user has access, False otherwise.
    """
    cur = _db.cursor()
    cur.execute(
        """
        SELECT 1 FROM SnippetPermissions
        WHERE SnippetID = ? AND UserID = ?
        """,
        [snippet_id, user_id],
    )
    return cur.fetchone() is not None

def get_snippets_user_has_access_to(user_id):
    """
    Returns a list of snippet IDs that a user has access to.
    """
    cur = _db.cursor()
    cur.execute(
        """
        SELECT SnippetID FROM SnippetPermissions
        WHERE UserID = ?
        """,
        [user_id],
    )
    return [row[0] for row in cur.fetchall()]

def get_all_users_with_permission(snippet_id):
    """
    Returns a list of users who have permission to view a specific snippet.
    
    Each entry contains:
    - "id": The user's integer ID.
    - "name": The user's name.
    """
    cur = _db.cursor()
    cur.execute(
        """
        SELECT U.ID, U.Name
        FROM SnippetPermissions AS SP
        JOIN User AS U ON SP.UserID = U.ID
        WHERE SP.SnippetID = ?
        """,
        [snippet_id],
    )
    
    return [{"id": row[0], "name": row[1]} for row in cur.fetchall()]

def get_all_users_excluding_current(current_user_id):
    """Fetches all users except the current user."""
    cur = _db.cursor()
    cur.execute(
        """
        SELECT ID, Name FROM User WHERE ID != ?
        """,
        [current_user_id],
    )
    return [{"id": row[0], "name": row[1]} for row in cur.fetchall()]

def get_tags(id):
    """
    Gets a Snippet's tags by integer ID.

    - "id": The id of the snippet.
    - "name": The name of the tag.
    """
    cur = _db.cursor()
    cur.execute(
        """
        SELECT
            *
        FROM TagUse
        WHERE SnippetID = ?
        ORDER BY TagName
        """,
        [id],
    )
    tags = cur.fetchall()

    return [
        {

            "id": tag[0],
            "name": tag[1],
        }
        for tag in tags
    ]

def update_snippet(id, user_id, name, code, description=None, old_description=None, delete_tags=None, new_tags=None):
    """updates Snippets and Tags"""
    cur = _db.cursor()

    # Update the Snippet
    cur.execute(
        """
        UPDATE Snippet
        SET 
            Name = ?,
            Code = ?,
            Description = ?,
            Date = datetime('now')
        WHERE ID = ? AND UserID = ?
        """,
        [name, code, description or "", id, user_id],
    )

    # Delete old tags
    if delete_tags is not None:
        cur.executemany(
            """
            DELETE FROM TagUse
            WHERE  
                SnippetID = ? AND 
                TagName = ?
            """,
            [(id, tag) for tag in delete_tags],
        )

    if new_tags is not None:
        cur.executemany(
            """
                INSERT INTO TagUse (SnippetID, TagName)
                VALUES (?, ?)
                """,
                [(id, tag) for tag in new_tags],
        )


    # Create a "summary" of the snippet description for smart search
    if description is not None:
        if  old_description is not None and description == old_description:
            return
        embedding = _get_transformer().encode(description)
        cur.execute(
            """UPDATE SnippetEmbedding
            SET
                Embedding = ?
            WHERE SnippetID = ?
            """,
            [embedding, id],
        )

    _db.commit()
    return id
