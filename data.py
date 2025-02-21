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

preset_tags = [
    "HTML",
    "CSS",
    "JavaScript",
    "Python",
    "Flask",
    "Django",
    "React",
    "Vue.js",
    "Code Snippet",
]


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
        PRAGMA foreign_keys = 1;
        BEGIN;
        CREATE TABLE IF NOT EXISTS User (
            ID INTEGER PRIMARY KEY,
            Name TEXT UNIQUE,
            PasswordHash TEXT,
            ProfilePicture BLOB,    -- For storing profile picture BLOB (binary large object)
            Bio TEXT,               -- User biography
            Description VARCHAR(250)
        );
        CREATE TABLE IF NOT EXISTS Snippet (
            ID INTEGER PRIMARY KEY,
            Name TEXT,
            Code TEXT,
            Description TEXT,
            UserID INTEGER REFERENCES User(ID) ON DELETE SET NULL,
            ParentSnippetID INTEGER REFERENCES Snippet(ID) ON DELETE SET NULL,
            Date,
            IsPublic BOOLEAN DEFAULT 0, --0 for private and 1 for public
            ShareableLink TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS TagUse (
            SnippetID INTEGER,
            TagName TEXT,
            PRIMARY KEY (SnippetID, TagName),
            FOREIGN KEY (SnippetID) REFERENCES Snippet(ID) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS Links (
            ID INTEGER PRIMARY KEY,
            UserID INTEGER,
            Platform TEXT,  -- e.g., "GitHub", "Discord"
            URL TEXT,       -- The actual link
            FOREIGN KEY (UserID) REFERENCES User(ID) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS SnippetPermissions (
            SnippetID INTEGER,
            UserID INTEGER,
            PRIMARY KEY (SnippetID, UserID),
            FOREIGN KEY (SnippetID) REFERENCES Snippet(ID) ON DELETE CASCADE,
            FOREIGN KEY (UserID) REFERENCES User(ID) ON DELETE CASCADE
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
        DROP TABLE IF EXISTS SnippetEmbedding;
        DROP TABLE IF EXISTS SnippetPermissions;
        DROP TABLE IF EXISTS Links;
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
                is_public=random.choice([True, False]),
            )


## USER INFO ###

def delete_user(id):
    """Deletes a user account. Returns `True` if the account was deleted, `False` otherwise."""
    cur = _db.cursor()
    cur.execute(
        """
        DELETE 
        FROM User
        WHERE ID = ?
        """,
        [id],
    )
    _db.commit()
    return True

def get_user_by_id(user_id):
    """
    Returns a dictionary of user data, or `None` if a user with the given ID does not exist.

    - "name": The user's name.
    - "password_hash": An argon2 hash of the user's password.
    - "profile_picture": The user's profile picture
    """

    cur = _db.cursor()
    cur.execute(
        """
        SELECT Name, PasswordHash, ProfilePicture
        FROM User
        WHERE ID == ?
        """,
        [user_id],
    )

    res = cur.fetchone()

    if res is None:
        return None
    else:
        return {"name": res[0], "password_hash": res[1], "profile_picture": res[2]}


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


def get_user_details(user_id):
    """
    Fetches details of a user by ID.
    
    Returns a dictionary with:
    - "name": The user's name.
    - "bio": The user's bio.
    - "profile_picture": The user's profile picture (returns None if not set).
    """
    cur = _db.cursor()
    cur.execute(
        """
        SELECT Name, Bio, ProfilePicture 
        FROM User 
        WHERE ID = ?
        """,
        [user_id],
    )

    res = cur.fetchone()
    if res is None:
        return None

    return {
        "name": res[0],
        "bio": res[1] if res[1] else "",
        "profile_picture": res[2],  # Return BLOB (frontend should handle display)
    }


## SNIPPETS ###


def create_snippet(
    name,
    code,
    user_id,
    description=None,
    tags=None,
    is_public=False,
    permitted_users=None,
    parent_snippet_id=None,
):
    """Creates a new snippet, returning its integer ID."""
    cur = _db.cursor()

    shareable_link = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO Snippet (Name, Code, Description, UserID, Date, IsPublic, ShareableLink, ParentSnippetID)
        VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?)
        """,
        [
            name,
            code,
            description or "",
            user_id,
            int(is_public),
            shareable_link,
            parent_snippet_id,
        ],
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
        # Remove empty strings and whitespace-only tags
        tags = [tag.strip() for tag in tags if tag.strip()]

        cur.executemany(
            """
            INSERT INTO TagUse (SnippetID, TagName)
            VALUES (?, ?)
            """,
            [(snippet_id, tag) for tag in tags],
        )

    if description is not None and is_public:
        embedding = _get_transformer().encode(description)
        cur.execute(
            """
            INSERT INTO SnippetEmbedding (SnippetID, Embedding)
            VALUES (?, ?)
            """,
            [snippet_id, embedding],
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
            "parent_snippet_id": snippet[5],
            "date": snippet[6],
            "is_public": bool(snippet[7]),  # Explicit conversion
            "tags": get_tags_for_snippet(snippet[0]),  # Fetch tags
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
    - "is_public": True if the snippet is public, False otherwise.
    - "tags": A list of tags that the snippet has.
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
            "tags": get_tags_for_snippet(snippet[0]),
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

    if names is str:
        names = [names]
    if tags is str:
        tags = [tags]
    if desc is str:
        desc = [desc]

    queries = []
    params = []

    # Snippet name includes any of the given names
    if names:
        name_match = "(" + " OR ".join(["Name LIKE ?"] * len(names)) + ")"
        queries.append(name_match)
        params.extend(["%" + name + "%" for name in names])

    # Snippet tags include all of the given tags
    if tags:
        tags_match = "(" + ",".join(["?"] * len(tags)) + ")"
        queries.append(
            f"""
            EXISTS (
                SELECT 1 FROM TagUse AS T
                WHERE ID = T.SnippetID
                AND T.TagName IN {tags_match}
            )
            """
        )
        params.extend(tags)

    # Snippet description includes any of the given description text
    if desc:
        desc_match = "(" + " OR ".join(["Description LIKE ?"] * len(desc)) + ")"
        queries.append(desc_match)
        params.extend(["%" + desc_term + "%" for desc_term in desc])

    # Ensure only accessible snippets are returned
    access_filter = """
        (IsPublic = 1 OR EXISTS (
            SELECT 1 FROM SnippetPermissions AS P
            WHERE P.SnippetID = ID AND P.UserID = ?
        ))
    """
    queries.append(access_filter)
    params.append(user_id)

    # Final query with filters applied
    query = f"""
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
        WHERE {" AND ".join(queries)}
        ORDER BY Date DESC
    """

    cur = _db.cursor()
    results = cur.execute(query, params)

    return [
        {
            "id": res[0],
            "name": res[1],
            "code": res[2],
            "description": res[3],
            "user_id": res[4],
            "parent_snippet_id": res[5],
            "date": res[6],
            "is_public": bool(res[7]),
            "tags": get_tags_for_snippet(res[0]),
            "is_description_match": False,
        }
        for res in results
    ]


def smart_search_snippets(query, user_id=None):
    """
    Leverages AI to return summaries of all snippets that match a query,
    but ensures only accessible snippets are returned.

    - "id": The integer ID of the snippet.
    - "name": The name of the snippet.
    - "code": The content of the snippet.
    - "description": The user-provided description.
    - "user_id": The author's integer ID.
    - "parent_snippet_id": The integer ID of the parent snippet or `None`.
    - "date": The date and time of this snippet's creation.
    - "is_public": True if the snippet is public, False otherwise.
    - "tags": A list of tags that the snippet has.
    - "is_description_match": A list of tags that the snippet has.
    """
    query_embedding = _get_transformer().encode(query)
    query_terms = ["%" + term.strip() + "%" for term in query.split(" ")]

    cur = _db.cursor()

    # Find snippets that have all query terms in their names
    cur.execute(
        f"""
        SELECT
            ID,
            Name,
            Code,
            Description,
            UserID,
            ParentSnippetID,
            Date,
            IsPublic,
            0
        FROM Snippet
        WHERE ({" AND ".join(["Name LIKE ?"] * len(query_terms))})
        AND (IsPublic = 1 OR EXISTS (
            SELECT 1 FROM SnippetPermissions WHERE SnippetID = Snippet.ID AND UserID = ?
        ))
        ORDER BY length(Name) ASC, Name
        LIMIT 30
        """,
        query_terms + [user_id],
    )
    name_matches = cur.fetchall()

    # Search by description embedding
    # Embeddings are only generated for public snippets
    cur.execute(
        """
        WITH DescMatches AS (
            SELECT SnippetID
            FROM SnippetEmbedding
            WHERE Embedding MATCH ? AND k = ?
            ORDER BY distance
        )
        SELECT
            Snippet.ID,
            Snippet.Name,
            Snippet.Code,
            Snippet.Description,
            Snippet.UserID,
            Snippet.ParentSnippetID,
            Snippet.Date,
            Snippet.IsPublic,
            1
        FROM DescMatches
        JOIN Snippet ON Snippet.ID = DescMatches.SnippetID
        """,
        [query_embedding, 35 - len(name_matches)],
    )
    desc_matches = cur.fetchall()

    results = [
        {
            "id": res[0],
            "name": res[1],
            "code": res[2],
            "description": res[3],
            "user_id": res[4],
            "parent_snippet_id": res[5],
            "date": res[6],
            "is_public": bool(res[7]),
            "tags": get_tags_for_snippet(res[0]),
            "is_description_match": bool(res[8]),
        }
        for res in itertools.chain(name_matches, desc_matches)
    ]
    return results


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


def clear_snippet_permission(snippet_id):
    """
    Revokes permission to view a snippet for all users except the owner.

    Returns the number of users revoked.
    """
    cur = _db.cursor()
    cur.execute(
        """
        DELETE FROM SnippetPermissions
        WHERE SnippetID = ?
        """,
        [snippet_id],
    )
    count = cur.rowcount
    _db.commit()
    return count


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


def get_all_users_with_permission(snippet_id, exlude_user = None):
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
        WHERE SP.SnippetID = ? AND U.ID != ?
        """,
        [snippet_id, exlude_user],
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
            TagName
        FROM TagUse
        WHERE SnippetID = ?
        ORDER BY TagName
        """,
        [id],
    )
    tags = cur.fetchall()

    return [tag[0] for tag in tags]


def update_snippet(
    id, user_id, name, code, description=None, tags=None, is_public=False, users=None
):
    cur = _db.cursor()

    # Remove empty tags before updating the database
    if tags:
        tags = [tag.strip() for tag in tags if tag.strip()]  # Ensure no empty tags
        
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
    cur.execute(
        """
        DELETE FROM TagUse
        WHERE SnippetID = ?
        """,
        [id],
    )

    # Add new tags
    if tags is not None and tags != "":
        cur.executemany(
            """
            INSERT INTO TagUse (SnippetID, TagName)
            VALUES (?, ?)
            """,
            [(id, tag) for tag in tags],
        )

    # Create a "summary" of the snippet description for smart searches
    # Only generate embeddings for public snippets
    cur.execute(
        """
        DELETE FROM SnippetEmbedding
        WHERE SnippetID = ?
        """,
        [id],
    )
    if description is not None and is_public:
        embedding = _get_transformer().encode(description)
        cur.execute(
            """
            INSERT INTO SnippetEmbedding (SnippetID, Embedding)
            VALUES (?, ?)
            """,
            [id, embedding],
        )

    _db.commit()

    if is_public:
        set_snippet_visibility(id, is_public)

    clear_snippet_permission(id)

    if users:
        for user in users:
            grant_snippet_permission(id, user)

    return id


def delete_snippet(id, user_id):
    """Delete Snippets and Tags"""
    cur = _db.cursor()

    # Delete the Snippet
    cur.execute(
        """
        DELETE FROM Snippet
        WHERE ID = ? AND UserID = ?
        """,
        [id, user_id],
    )
    cur.execute(
        """
        DELETE FROM TagUse
        WHERE  
            SnippetID = ?
        """,
        [id],
    )

    _db.commit()
