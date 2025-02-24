"""
Stores user login information.
"""

import os
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


def init(app, login_view):
    login_manager.init_app(app)
    login_manager.login_view = login_view


def get_secret_key():
    try:
        file = open("secret_key.bin", "rb")
        return file.read()
    except FileNotFoundError:
        key = os.urandom(32)
        with open("secret_key.bin", "xb") as file:
            file.write(key)
        return key

def get_current_id_or_none():
    if flask_login.current_user.is_authenticated:
        return flask_login.current_user.id
    else:
        return None

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
    res = data.get_user_by_id(user_id)

    if res is None:
        return None
    else:
        return User(user_id, res["name"], res["password_hash"])


def try_login(username, password):
    """
    Attempts to retrieve a User from a username and password pair.
    If the user does not exist or the password does not match, then None is returned.
    """
    if username is None or username == "" or password is None or password == "":
        return None

    # Fetch account info by name
    res = data.get_user_by_name(username)

    # Verify that the password matches
    try:
        password_hasher.verify(res["password_hash"], password)
        return User(res["id"], res["name"], res["password_hash"])
    except:
        return None


def try_sign_up(username, password):
    """
    Attempts to create a new user account from a username and password pair.
    If the username was in use, then None is returned.
    """
    if username is None or username == "" or password is None or password == "":
        return None

    # Create the new account
    password_hash = password_hasher.hash(password)
    data.create_user(username, password_hash)

    # Log in with the new account
    return try_login(username, password)
