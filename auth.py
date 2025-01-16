"""
Stores user login information.
"""

import flask_login
import argon2
import data

login_manager = flask_login.LoginManager()
password_hasher = argon2.PasswordHasher()

class User(flask_login.UserMixin):
    def __init__(self, id, name, password_hash):
        self.id = id
        self.name = name
        self.password_hash = password_hash


def init(app):
    login_manager.init_app(app)


def get_username_error(username):
    """
    Returns an error message if a username fails to meet requirements.
    Otherwise, returns None.
    """
    if username is None or username == "":
        return "Username must not be empty!"
    if len(username) > 20:
        return "Username must be 20 or fewer characters!"
    else:
        return None


def get_password_error(password):
    """
    Returns an error message if a password fails to meet security requirements.
    Otherwise, returns None.
    """
    if password is None or password == "":
        return "Password must not be empty!"
    elif len(password) < 8:
        return "Password must be at least 8 characters!"
    elif len(password) > 60:
        return "Password must be at most 60 characters!"
    else:
        return None


@login_manager.user_loader
def load_user(user_id):
    """
    Fetch a user by ID, returning None if that user does not exist.
    """
    cur = data.db.cursor()
    cur.execute(
        """
        SELECT Name, PasswordHash
        FROM User
        WHERE ID == ?
        """, [ user_id ])
    
    res = cur.fetchone()

    if res is None:
        return None
    else:
        return User(user_id, res[0], res[1])


def try_login(username, password):
    """
    Attempts to retrieve a User from a username and password pair.
    If the user does not exist or the password does not match, then None is returned.
    """
    if username is None or username == "" or password is None or password == "":
        return None
    
    # Fetch account info by name
    cur = data.db.cursor()
    cur.execute(
        """
        SELECT ID, Name, PasswordHash
        FROM User
        WHERE Name == ?
        """, [ username ]
    )
    res = cur.fetchone()

    # Verify that the password matches
    try:
        password_hasher.verify(res[2], password)
        print("Logged in as", res[0])
        return User(int(res[0]), res[1], res[2])
    except:
        return None


def try_sign_up(username, password):
    """
    Attempts to create a new user account from a username and password pair.
    If the username was in use, then None is returned.
    """
    if username is None or username == "" or password is None or password == "":
        return None

    # Fail if an account with this name already exists
    cur = data.db.cursor()
    cur.execute("SELECT ID FROM User WHERE Name == ?", [ username ])
    if cur.fetchone() is not None:
        return None

    # Create the new account
    password_hash = password_hasher.hash(password)
    cur.execute(
        """
        INSERT INTO User(Name, PasswordHash)
        VALUES(?, ?)
        """, [ username, password_hash ]
    )
    data.db.commit()
    print("Signed up as", username)

    # Log in with the new account
    return try_login(username, password)
