"""
Defines the application's databases.
"""

import random
import sqlite3
import sqlite_vec
import os
import csv
import uuid  # For generating unique shareable links
import mock_data

preset_tags: list[str] = []
with open("tags_normalized.csv") as tags_file:
    reader = csv.reader(tags_file)
    for row in reader:
        preset_tags.append(row[0])
preset_tags.sort()

_desc_transformer = None


def preload_transformer():
    global _desc_transformer
    if _desc_transformer is None:
        from sentence_transformers import SentenceTransformer

        _desc_transformer = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )


def _get_transformer():
    preload_transformer()
    return _desc_transformer


class Data:
    def __init__(self):
        """Connect to the database, creating it if necessary."""
        if not os.path.exists("databases"):
            os.mkdir("databases")
        _db_path = os.path.join("databases", "snippet_oracle.db")

        self._db = sqlite3.connect(_db_path)
        self._db.enable_load_extension(True)
        sqlite_vec.load(self._db)
        self._db.enable_load_extension(False)

        self.generate_embeddings = True

        self._init_db()

    def close(self):
        """Close the database connection."""
        self._db.close()

    def _init_db(self):
        """Initialize the database's tables."""
        cur = self._db.cursor()

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
            CREATE TABLE IF NOT EXISTS Comments (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                SnippetID INTEGER NOT NULL,
                UserID INTEGER NOT NULL,
                ParentCommentID INTEGER DEFAULT NULL,  -- New field for replies
                Content TEXT NOT NULL,
                Date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (SnippetID) REFERENCES Snippet(ID) ON DELETE CASCADE,
                FOREIGN KEY (UserID) REFERENCES User(ID) ON DELETE CASCADE,
                FOREIGN KEY (ParentCommentID) REFERENCES Comments(ID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS Like (
                SnippetID INTEGER NOT NULL,
                UserID INTEGER NOT NULL,
                FOREIGN KEY (SnippetID) REFERENCES Snippet(ID) ON DELETE CASCADE,
                FOREIGN KEY (UserID) REFERENCES User(ID) ON DELETE CASCADE,
                UNIQUE (SnippetID, UserID)
            );
            COMMIT;
            """
        )

    ## GENERAL ##

    def reset(self):
        """Clears all tables in the database."""
        cur = self._db.cursor()
        cur.executescript(
            """
            PRAGMA foreign_keys = 0;
            BEGIN;
            DROP TABLE IF EXISTS SnippetEmbedding;
            DROP TABLE IF EXISTS SnippetPermissions;
            DROP TABLE IF EXISTS Links;
            DROP TABLE IF EXISTS TagUse;
            DROP TABLE IF EXISTS Snippet;
            DROP TABLE IF EXISTS User;
            DROP TABLE IF EXISTS Like;
            COMMIT;
            PRAGMA foreign_keys = 1;
            """
        )
        self._init_db()

    def populate(self):
        """Fills all tables with a bunch of fake data."""

        for _ in range(50):
            user_name = mock_data.username()
            self.create_user(user_name, "N/A")
            user_id = self.get_user_by_name(user_name)["id"]

            for _ in range(random.randint(0, 20)):
                self.create_snippet(
                    name=mock_data.title(),
                    code=mock_data.code(),
                    user_id=user_id,
                    description=mock_data.paragraph(),
                    tags=mock_data.tags(),
                    is_public=random.choice([True, False]),
                )

    ## USER INFO ###

    def delete_user(self, id):
        """Deletes a user account. Returns `True` if the account was deleted, `False` otherwise."""
        cur = self._db.cursor()
        cur.execute(
            """
            DELETE 
            FROM User
            WHERE ID = ?
            """,
            [id],
        )
        self._db.commit()
        return True

    def get_user_by_id(self, user_id):
        """
        Returns a dictionary of user data, or `None` if a user with the given ID does not exist.

        - "name": The user's name.
        - "password_hash": An argon2 hash of the user's password.
        - "profile_picture": The user's profile picture
        """

        cur = self._db.cursor()
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

    def get_user_by_name(self, name):
        """
        Returns a dictionary of user data, or `None` if a user with the given name does not exist.

        - "id": The user's integer ID.
        - "name": The user's name.
        - "password_hash": An argon2 hash of the user's password.
        """

        cur = self._db.cursor()
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

    def create_user(self, name, password_hash):
        """Creates a new user account. Returns `True` if the account was created, `False` otherwise."""

        cur = self._db.cursor()
        try:
            cur.execute(
                """
                INSERT INTO User(Name, PasswordHash)
                VALUES(?, ?)
                """,
                [name, password_hash],
            )
            self._db.commit()
            return True
        except sqlite3.IntegrityError:
            # Raised when Name was not unique
            return False

    def get_user_details(self, user_id):
        """
        Fetches details of a user by ID.

        Returns a dictionary with:
        - "name": The user's name.
        - "bio": The user's bio.
        - "profile_picture": The user's profile picture (returns None if not set).
        """
        if user_id is None:
            return None

        cur = self._db.cursor()
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

        cur.execute(
            """
            SELECT Platform, URL 
            FROM Links 
            WHERE UserID = ?
            """,
            [user_id],
        )

        social_links = [{"platform": row[0], "url": row[1]} for row in cur.fetchall()]

        return {
            "name": res[0],
            "bio": res[1] if res[1] else "",
            "profile_picture": res[2]
            if res[2]
            else "default_image.png",  # Return BLOB (frontend should handle display)
            "social_links": social_links,
        }

    def get_popular_users(self):
        """
        Gets the Top 10 Most Popular Users
        Returns Username, Profle Picture for card
        """
        cur = self._db.cursor()
        results = cur.execute(
            """
            SELECT User.Name, User.ProfilePicture
            FROM Snippet, User
            WHERE Snippet.IsPublic = 1 AND Snippet.UserID = User.ID 
            GROUP BY Snippet.UserID
            ORDER BY SUM ((SELECT COUNT(*) FROM Like WHERE Like.SnippetID = Snippet.ID)) DESC, User.Name
            LIMIT 10
            """
        )

        if results is None:
            return None
        else:
            return [{"name": res[0], "profile_picture": res[1]} for res in results]

    ## SNIPPETS ###

    def create_snippet(
        self,
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
        cur = self._db.cursor()

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
            permitted_users = [
                int(uid) for uid in permitted_users if str(uid).isdigit()
            ]
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

        if (
            description is not None
            and description != ""
            and is_public
            and self.generate_embeddings
        ):
            embedding = _get_transformer().encode(description)
            cur.execute(
                """
                INSERT INTO SnippetEmbedding (SnippetID, Embedding)
                VALUES (?, ?)
                """,
                [snippet_id, embedding],
            )

        self._db.commit()

        # Posters like their own snippets by default
        self.add_like(snippet_id, user_id)

        return snippet_id

    def get_snippet(self, snippet_id, viewer_id=None):
        cur = self._db.cursor()

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
            (snippet_id, viewer_id, snippet_id, viewer_id),
        )

        snippet = cur.fetchone()

        if snippet:
            user_details = self.get_user_details(snippet[4])

            return {
                "id": snippet[0],
                "name": snippet[1],
                "code": snippet[2],
                "description": snippet[3],
                "user_id": snippet[4],
                "parent_snippet_id": snippet[5],
                "date": snippet[6],
                "is_public": bool(snippet[7]),  # Explicit conversion
                "tags": self.get_tags_for_snippet(snippet[0]),  # Fetch tags
                "shareable_link": snippet[8],
                "likes": self.get_likes(snippet[0]),
                "is_liked": self.is_liked(snippet[0], viewer_id),
                "author": user_details,  # Include (name, bio, profile_picture)
            }

        return None  # Snippet not found or not accessible

    def get_user_snippets(self, user_id, viewer_id=None):
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
        cur = self._db.cursor()
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

        snippets_list = []
        for snippet in snippets:
            user_details = self.get_user_details(snippet[4])

            snippets_list.append(
                {
                    "id": snippet[0],
                    "name": snippet[1],
                    "code": snippet[2],
                    "description": snippet[3],
                    "user_id": snippet[4],
                    "parent_snippet_id": snippet[5],
                    "date": snippet[6],
                    "is_public": bool(snippet[7]),
                    "tags": self.get_tags_for_snippet(snippet[0]),
                    "likes": self.get_likes(snippet[0]),
                    "is_liked": self.is_liked(snippet[0], viewer_id),
                    "author": user_details,  # Include (name, bio, profile_picture)
                }
            )

        return snippets_list

    def set_snippet_visibility(self, snippet_id, is_public):
        """
        Set a snippet's visibility and removes shareable link if it becomes public
        """

        cur = self._db.cursor()
        cur.execute(
            """
            UPDATE Snippet
            SET IsPublic = ?
            WHERE ID = ?
            """,
            [is_public, snippet_id],
        )
        self._db.commit()

    def get_snippet_id_by_shareable_link(self, link):
        """
        Fetches snippet using its unique shareable link
        """

        cur = self._db.cursor()
        cur.execute(
            "SELECT ID, IsPublic FROM Snippet WHERE ShareableLink = ?",
            [link],
        )
        snippet = cur.fetchone()

        if snippet is None:
            return None
        else:
            return {
                "id": snippet[0],
                "is_public": bool(snippet[1]),
            }

    def get_popular_public_snippets(self, viewer_id=None):
        """
        Gets the Top 10 Most Popular Snippets
        Returns Snippet Card Info
        """
        cur = self._db.cursor()
        results = cur.execute(
            """
            SELECT Snippet.ID, Snippet.Name, Snippet.Code, Snippet.Description,
                Snippet.UserID, Snippet.ParentSnippetID, Snippet.Date, Snippet.IsPublic,
                (SELECT COUNT(*) FROM Like WHERE Like.SnippetID = Snippet.ID) AS like_count
            FROM Snippet
            WHERE Snippet.IsPublic = 1
            ORDER BY like_count DESC, Snippet.Date DESC
            LIMIT 10
            """
        )

        snippets_list = []
        for res in results:
            user_details = self.get_user_details(res[4])  # Fetch user details
            snippets_list.append(
                {
                    "id": res[0],
                    "name": res[1],
                    "code": res[2],
                    "description": res[3],
                    "user_id": res[4],
                    "parent_snippet_id": res[5],
                    "date": res[6],
                    "is_public": bool(res[7]),
                    "tags": self.get_tags_for_snippet(res[0]),  # Fetch snippet tags
                    "likes": res[8],  # Sort by like count
                    "is_liked": self.is_liked(
                        res[0], viewer_id
                    ),  # Check if the user liked it
                    "author": user_details,  # Attach user details
                }
            )

        return snippets_list

    def get_recent_shared_snippets(self, user_id=None):
        """
        Gets the Top 10 Most Popular Snippets
        Returns Snippet Card Info
        """
        cur = self._db.cursor()
        results = cur.execute(
            """
            SELECT Snippet.ID, Snippet.Name, Snippet.Code, Snippet.Description,
                Snippet.UserID, Snippet.ParentSnippetID, Snippet.Date, Snippet.IsPublic
            FROM Snippet
            WHERE Snippet.ID IN 
              (SELECT SnippetID FROM SnippetPermissions
                WHERE UserID = ?)
            ORDER BY Snippet.Date DESC
            LIMIT 10
            """,
            [user_id],
        )

        snippets_list = []
        for res in results:
            user_details = self.get_user_details(res[4])  # Fetch user details
            snippets_list.append(
                {
                    "id": res[0],
                    "name": res[1],
                    "code": res[2],
                    "description": res[3],
                    "user_id": res[4],
                    "parent_snippet_id": res[5],
                    "date": res[6],
                    "is_public": bool(res[7]),
                    "tags": self.get_tags_for_snippet(res[0]),  # Fetch snippet tags
                    "likes": res[8],  # Sort by like count
                    "is_liked": self.is_liked(
                        res[0], user_id
                    ),  # Check if the user liked it
                    "author": user_details,  # Attach user details
                }
            )

        return snippets_list

    def search_tags(self, query):
        """Returns a list of all preset tags matching the search query."""
        query = query.lower()
        return [tag for tag in preset_tags if query in tag.lower()]

    def search_users(self, query):
        """
        Returns a list of all users with names matching the search query.

        - "name": The user's name.
        - "profile_picture": The user's profile picture.
        """

        cur = self._db.cursor()
        results = cur.execute(
            """
            SELECT Name, ProfilePicture 
            FROM User 
            WHERE Name LIKE ?
            ORDER BY Name
            """,
            ["%" + query + "%"],
        )

        return [{"name": res[0], "profile_picture": res[1]} for res in results]

    def search_snippets(
        self,
        terms=None,
        include_tags=None,
        exclude_tags=None,
        usernames=None,
        viewer_id=None,
        public=True,
    ):
        """
        Searches snippets based on:
        - Prioritizes name matches before description matches.
        - Breaks ties using likes.
        - Exact (case-insensitive) match for authors; falls back to similar matches if no exact match.
        - Prioritizes exact tag matches, falls back to prefix match if no exact matches exist.
        """

        if isinstance(terms, str):
            terms = [terms]
        if isinstance(include_tags, str):
            include_tags = [include_tags]
        if isinstance(exclude_tags, str):
            exclude_tags = [exclude_tags]
        if isinstance(usernames, str):
            usernames = [usernames]

        # Convert usernames and tags to lowercase for case-insensitive search
        usernames = [username.lower() for username in usernames] if usernames else []
        include_tags = [tag.lower() for tag in include_tags] if include_tags else []
        exclude_tags = [tag.lower() for tag in exclude_tags] if exclude_tags else []

        queries = []
        params = []
        cur = self._db.cursor()

        # Name & Description - Fuzzy Search (Prioritize Name Matches)
        name_priority = "0 AS name_priority"
        if terms:
            name_priority = "CASE WHEN LOWER(Snippet.Name) LIKE LOWER(?) THEN 1 ELSE 0 END AS name_priority"
            fuzzy_match = " OR ".join(
                [
                    "(LOWER(Snippet.Name) LIKE LOWER(?) OR LOWER(Snippet.Description) LIKE LOWER(?))"
                ]
                * len(terms)
            )
            queries.append(f"({fuzzy_match})")
            for term in terms:
                params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])

        # Case-Insensitive User Search (Exact First, Then Fallback to Similar)
        if usernames:
            exact_user_query = """
                SELECT COUNT(*) FROM User WHERE LOWER(Name) IN ({})
            """.format(",".join(["?"] * len(usernames)))

            cur.execute(exact_user_query, usernames)
            exact_user_count = cur.fetchone()[0]

            if exact_user_count > 0:
                # If exact match exists, return only snippets from the exact user
                queries.append(
                    """
                    Snippet.UserID IN (
                        SELECT ID FROM User WHERE LOWER(Name) IN ({})
                    )
                """.format(",".join(["?"] * len(usernames)))
                )
                params.extend(usernames)
            else:
                # If no exact match, fall back to similar username search
                queries.append("""
                    Snippet.UserID IN (
                        SELECT ID FROM User WHERE LOWER(Name) LIKE LOWER(?)
                    )
                """)
                params.append(
                    f"%{usernames[0]}%"
                )  # Use the first username for fuzzy matching

        # Tag Filtering (Exact Match First, Prefix Match if No Exact Matches Found)
        if include_tags:
            exact_match_query = """
                SELECT COUNT(*) FROM Snippet
                WHERE Snippet.ID IN (
                    SELECT SnippetID FROM TagUse WHERE LOWER(TagName) IN ({})
                )
            """.format(",".join(["?"] * len(include_tags)))

            exact_params = list(include_tags)
            cur.execute(exact_match_query, exact_params)
            exact_match_count = cur.fetchone()[0]

            if exact_match_count > 0:
                queries.append(
                    """
                    Snippet.ID IN (
                        SELECT SnippetID FROM TagUse WHERE LOWER(TagName) IN ({})
                    )
                """.format(",".join(["?"] * len(include_tags)))
                )
                params.extend(exact_params)
            else:
                # If no exact matches, fall back to prefix search
                prefix_conditions = ["LOWER(TagName) LIKE LOWER(?)"] * len(include_tags)
                prefix_match_query = """
                    Snippet.ID IN (
                        SELECT SnippetID FROM TagUse WHERE {}
                    )
                """.format(" OR ".join(prefix_conditions))

                prefix_params = [tag + "%" for tag in include_tags]
                queries.append(prefix_match_query)
                params.extend(prefix_params)

        # Handle Exclude Tags (-tag)
        if exclude_tags:
            exclude_tags_match = ",".join(["?"] * len(exclude_tags))
            queries.append(f"""
                Snippet.ID NOT IN (
                    SELECT DISTINCT SnippetID FROM TagUse WHERE LOWER(TagUse.TagName) IN ({exclude_tags_match})
                )
            """)
            params.extend(exclude_tags)

        # Access control filter (public/private visibility)
        if public:
            access_filter = """
                (Snippet.IsPublic = 1 OR EXISTS (
                    SELECT 1 FROM SnippetPermissions AS P
                    WHERE P.SnippetID = Snippet.ID AND P.UserID = ?
                ))
            """
        else:
            access_filter = "Snippet.UserID = ?"
        queries.append(access_filter)
        params.append(viewer_id)

        # Ensure there's at least one condition to prevent empty WHERE clause
        if not queries:
            queries.append(
                "1=1"
            )  # This prevents SQL syntax errors if no filters are applied

        # Final SQL query with ordering: Name Matches First, Then Sort by Likes
        query = f"""
            SELECT Snippet.ID, Snippet.Name, Snippet.Code, Snippet.Description,
                Snippet.UserID, Snippet.ParentSnippetID, Snippet.Date, Snippet.IsPublic,
                (SELECT COUNT(*) FROM Like WHERE Like.SnippetID = Snippet.ID) AS like_count,
                {name_priority}
            FROM Snippet
            WHERE {" AND ".join(queries)}
            ORDER BY name_priority DESC, like_count DESC, Snippet.Date DESC
            LIMIT 50
        """

        cur.execute(query, params)
        results = cur.fetchall()

        snippets_list = []
        for res in results:
            user_details = self.get_user_details(res[4])  # Fetch user details
            snippets_list.append(
                {
                    "id": res[0],
                    "name": res[1],
                    "code": res[2],
                    "description": res[3],
                    "user_id": res[4],
                    "parent_snippet_id": res[5],
                    "date": res[6],
                    "is_public": bool(res[7]),
                    "tags": self.get_tags_for_snippet(res[0]),  # Fetch snippet tags
                    "likes": res[8],  # Sort by like count
                    "is_liked": self.is_liked(
                        res[0], viewer_id
                    ),  # Check if the user liked it
                    "author": user_details,  # Attach user details
                }
            )

        return snippets_list

    def smart_search_snippets(self, query, viewer_id=None):
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
        - "likes": The number of likes this snippet has.
        - "is_liked": Whether the viewer has liked this snippet.
        - "author": The author's user details.
        """
        query_embedding = _get_transformer().encode(query)
        cur = self._db.cursor()

        # Search by description embedding
        # Embeddings are only generated for public snippets
        cur.execute(
            """
            WITH DescMatches AS (
                SELECT SnippetID
                FROM SnippetEmbedding
                WHERE Embedding MATCH ? AND k = 50
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
                Snippet.IsPublic
            FROM DescMatches
            JOIN Snippet ON Snippet.ID = DescMatches.SnippetID
            """,
            [query_embedding],
        )

        results = []
        for res in cur.fetchall():
            results.append(
                {
                    "id": res[0],
                    "name": res[1],
                    "code": res[2],
                    "description": res[3],
                    "user_id": res[4],
                    "parent_snippet_id": res[5],
                    "date": res[6],
                    "is_public": bool(res[7]),
                    "tags": self.get_tags_for_snippet(res[0]),
                    "likes": self.get_likes(res[0]),
                    "is_liked": self.is_liked(res[0], viewer_id),
                    "author": self.get_user_details(res[4]),
                }
            )

        return results

    def grant_snippet_permission(self, snippet_id, user_id):
        """
        Grants a user permission to view a snippet.

        Returns True if permission was granted, False if it already exists.
        """
        cur = self._db.cursor()
        try:
            cur.execute(
                """
                INSERT INTO SnippetPermissions (SnippetID, UserID)
                VALUES (?, ?)
                """,
                [snippet_id, user_id],
            )
            self._db.commit()
            return True
        except sqlite3.IntegrityError:
            # Permission already exists
            return False

    def revoke_snippet_permission(self, snippet_id, user_id):
        """
        Revokes a user's permission to view a snippet.

        Returns True if permission was revoked, False if the permission did not exist.
        """
        cur = self._db.cursor()
        cur.execute(
            """
            DELETE FROM SnippetPermissions
            WHERE SnippetID = ? AND UserID = ?
            """,
            [snippet_id, user_id],
        )
        if cur.rowcount > 0:
            self._db.commit()
            return True
        return False

    def clear_snippet_permission(self, snippet_id):
        """
        Revokes permission to view a snippet for all users except the owner.

        Returns the number of users revoked.
        """
        cur = self._db.cursor()
        cur.execute(
            """
            DELETE FROM SnippetPermissions
            WHERE SnippetID = ?
            """,
            [snippet_id],
        )
        count = cur.rowcount
        self._db.commit()
        return count

    def user_has_permission(self, snippet_id, user_id):
        """
        Checks if a user has permission to view a snippet.

        Returns True if the user has access, False otherwise.
        """
        cur = self._db.cursor()
        cur.execute(
            """
            SELECT 1 FROM SnippetPermissions
            WHERE SnippetID = ? AND UserID = ?
            """,
            [snippet_id, user_id],
        )
        return cur.fetchone() is not None

    def get_snippets_user_has_access_to(self, user_id):
        """
        Returns a list of snippet IDs that a user has access to.
        """
        cur = self._db.cursor()
        cur.execute(
            """
            SELECT SnippetID FROM SnippetPermissions
            WHERE UserID = ?
            """,
            [user_id],
        )
        return [row[0] for row in cur.fetchall()]

    def get_all_users_with_permission(self, snippet_id, exlude_user=None):
        """
        Returns a list of users who have permission to view a specific snippet.

        Each entry contains:
        - "id": The user's integer ID.
        - "name": The user's name.
        """
        cur = self._db.cursor()
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

    def get_all_users_excluding_current(self, current_user_id):
        """Fetches all users except the current user."""
        cur = self._db.cursor()
        cur.execute(
            """
            SELECT ID, Name FROM User WHERE ID != ?
            """,
            [current_user_id],
        )
        return [{"id": row[0], "name": row[1]} for row in cur.fetchall()]

    # Finds the tags by snippetID
    def get_tags_for_snippet(self, snippet_id):
        """
        Fetches all tags associated with a given snippet.
        """
        cur = self._db.cursor()
        cur.execute(
            """
            SELECT TagName FROM TagUse WHERE SnippetID = ?
            """,
            [snippet_id],
        )
        tags = cur.fetchall()

        return [tag[0] for tag in tags]  # Convert tuple list to a simple list

    def get_tags(self, id):
        """
        Gets a Snippet's tags by integer ID.

        - "id": The id of the snippet.
        - "name": The name of the tag.
        """
        cur = self._db.cursor()
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

    def get_popular_public_tags(self):
        """
        Gets The Top 10 Most Popular Global Snippets
        Returns a list of tag and count
        """
        cur = self._db.cursor()
        cur.execute(
            """
            SELECT TAGUSE.TAGNAME, count(*) AS tagCount
            FROM TAGUSE
            GROUP BY TAGUSE.TAGNAME 
            ORDER BY tagCount DESC
            LIMIT 10;
            """,
        )
        return [row[0] for row in cur.fetchall()]

    def get_profile_public_tags(self, user_id):
        """
        Takes user_id and returns top 10 tags on public facing snippets
        Returns top 10
        """
        cur = self._db.cursor()
        cur.execute(
            """
            SELECT TAGUSE.TAGNAME, count(*) AS tagCount
            FROM TAGUSE
            WHERE TAGUSE.SNIPPETID 
            IN (
              SELECT SNIPPET.ID 
              FROM SNIPPET
              WHERE SNIPPET.USERID  = :ok
              AND SNIPPET.ISPUBLIC = 1
            )
            GROUP BY TAGUSE.TAGNAME 
            ORDER BY tagCount DESC
            LIMIT 10;
            """,
            [user_id],
        )
        return [{"Name": row[0], "Count": row[1]} for row in cur.fetchall()]

    def get_profile_all_tags(self, user_id):
        """
        Takes user_id and returns top 10 tags based on all their snippest
        Returns top 10
        """
        cur = self._db.cursor()
        cur.execute(
            """
          SELECT TAGUSE.TAGNAME, count(*) AS tagCount
          FROM TAGUSE
          WHERE TAGUSE.SNIPPETID 
          IN (
            SELECT SNIPPET.ID 
            FROM SNIPPET
            WHERE SNIPPET.USERID  = :ok
            AND SNIPPET.ISPUBLIC = 1
          )
          GROUP BY TAGUSE.TAGNAME 
          ORDER BY tagCount DESC
          LIMIT 10;
          """,
            [user_id],
        )
        return [{"Name": row[0], "Count": row[1]} for row in cur.fetchall()]

    # Snippet Modification
    def update_snippet(
        self,
        id,
        user_id,
        name,
        code,
        description=None,
        tags=None,
        is_public=False,
        users=None,
    ):
        cur = self._db.cursor()
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
        if (
            description is not None
            and description != ""
            and is_public
            and self.generate_embeddings
        ):
            embedding = _get_transformer().encode(description)
            cur.execute(
                """
                INSERT INTO SnippetEmbedding (SnippetID, Embedding)
                VALUES (?, ?)
                """,
                [id, embedding],
            )

        self._db.commit()

        self.set_snippet_visibility(id, is_public)
        self.clear_snippet_permission(id)

        if not is_public:
            if users:
                for user in users:
                    self.grant_snippet_permission(id, user)

        return id

    def delete_snippet(self, id, user_id):
        """Delete Snippets and Tags"""
        cur = self._db.cursor()

        # Delete the Snippet
        cur.execute(
            """
            DELETE FROM Snippet
            WHERE ID = ? AND UserID = ?
            """,
            [id, user_id],
        )

        self._db.commit()

    # Comment Functions
    def add_comment(self, snippet_id, user_id, comment, parent_id=None):
        """Adds a comment or reply to a snippet."""
        cur = self._db.cursor()
        cur.execute(
            """
            INSERT INTO Comments (SnippetID, UserID, Content, ParentCommentID)
            VALUES (?, ?, ?, ?)
            """,
            (snippet_id, user_id, comment, parent_id),
        )
        self._db.commit()

    def get_comments(self, snippet_id):
        """Fetches all comments and their replies for a snippet."""
        cur = self._db.cursor()
        cur.execute(
            """
            SELECT Comments.ID, Comments.Content, Comments.Date, Comments.UserID, Comments.ParentCommentID, 
                User.Name, User.ProfilePicture
            FROM Comments
            JOIN User ON Comments.UserID = User.ID
            WHERE Comments.SnippetID = ?
            ORDER BY Comments.ParentCommentID NULLS FIRST, Comments.Date ASC
            """,
            [snippet_id],
        )

        comments = cur.fetchall()
        comment_tree = {}
        for row in comments:
            comment_data = {
                "id": row[0],
                "content": row[1],
                "date": row[2],
                "user_id": int(row[3]),
                "parent_id": row[4],
                "user_name": row[5],
                "profile_picture": row[6],
                "replies": [],
            }

            if comment_data["parent_id"] is None:
                comment_tree[comment_data["id"]] = comment_data
            else:
                if comment_data["parent_id"] in comment_tree:
                    comment_tree[comment_data["parent_id"]]["replies"].append(
                        comment_data
                    )
                else:
                    comment_tree[comment_data["parent_id"]] = {
                        "replies": [comment_data]
                    }
        return list(comment_tree.values())

    def get_comment_by_id(self, comment_id):
        """Fetches a specific comment by its ID."""
        cur = self._db.cursor()
        cur.execute(
            """
            SELECT ID, SnippetID, UserID, Content, Date 
            FROM Comments 
            WHERE ID = ?
            """,
            [comment_id],
        )

        comment = cur.fetchone()
        if comment:
            return {
                "id": comment[0],
                "snippet_id": comment[1],
                "user_id": comment[2],
                "content": comment[3],
                "date": comment[4],
            }
        return None  # Comment not found

    def delete_comment(self, comment_id):
        """Deletes a comment and all its replies recursively."""
        cur = self._db.cursor()

        cur.execute(
            """
            SELECT ID FROM Comments WHERE ParentCommentID = ?
            """,
            [comment_id],
        )
        replies = cur.fetchall()

        # Recursively delete each reply
        for reply in replies:
            self.delete_comment(reply[0])

        # Finally, delete the parent comment itself
        cur.execute(
            """
            DELETE FROM Comments WHERE ID = ?
            """,
            [comment_id],
        )

        self._db.commit()

    # Like Functions
    def add_like(self, snippet_id, user_id):
        """
        Adds a like to a snippet.

        Returns True if the like was added, False if the user had already liked the snippet or the snippet was not found.
        """
        cur = self._db.cursor()

        try:
            cur.execute(
                "INSERT INTO Like(SnippetID, UserID) VALUES (?, ?)",
                [snippet_id, user_id],
            )
        except sqlite3.IntegrityError:
            return False

        self._db.commit()
        return True

    def remove_like(self, snippet_id, user_id):
        """Removes a like from a snippet, if one existed from the given user."""
        cur = self._db.cursor()
        cur.execute(
            "DELETE FROM Like WHERE SnippetID = ? AND UserID = ?", [snippet_id, user_id]
        )
        self._db.commit()

    def get_likes(self, snippet_id):
        """Returns the number of likes a snippet has."""

        cur = self._db.cursor()
        cur.execute("SELECT count(*) FROM Like WHERE SnippetID = ?", [snippet_id])

        return cur.fetchone()[0]

    def is_liked(self, snippet_id, user_id):
        """Returns True if the user has liked the snippet, False otherwise."""
        if user_id is None:
            return False

        cur = self._db.cursor()
        cur.execute(
            "SELECT count(*) FROM Like WHERE SnippetID = ? AND UserID = ?",
            [snippet_id, user_id],
        )
        return cur.fetchone()[0] > 0
