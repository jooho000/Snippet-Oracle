"""
The main Flask module for Snippet Oracle.
"""

# Some notes from Zach:
#   This is the web app framework https://flask.palletsprojects.com/en/stable/quickstart/
#   This is how you set up templates https://flask.palletsprojects.com/en/stable/patterns/templateinheritance/
#   This is the CSS library we're using https://bulma.io/documentation/
#   This is the database system we're using for development https://docs.python.org/3/library/sqlite3.html

import flask
import flask_login
import click
import data
import auth
from flask import jsonify, request


app = flask.Flask("snippet_oracle")
auth.init(app, "login")
app.secret_key = auth.get_secret_key()


@app.cli.command("reset-db")
def create_user():
    data.reset()


@app.cli.command("populate-db")
def create_user():
    data.reset()
    data.populate()


@app.route("/")
def index():
    return flask.render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")

        user = auth.try_login(username, password)

        if username is None or username == "":
            flask.flash("Input a username!")
        elif password is None or password == "":
            flask.flash("Input a password!")
        elif user is None:
            flask.flash("Invalid username or password!")

        # TODO: Redirect to flask.request.args.get("next") instead
        # This isn't implement right now because it's a potential attack vector
        if user is None:
            return flask.render_template("login.html", username=username)
        else:
            flask_login.login_user(user)
            return flask.redirect(flask.url_for("index"))

    else:
        return flask.render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if flask.request.method == "POST":
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")
        repeat_password = flask.request.form.get("repeatPassword")

        # Allow logging in, if the user is on this page by mistake
        user = auth.try_login(username, password)
        if user is not None:
            flask_login.login_user(user)
            return flask.redirect(flask.url_for("index"))

        # Validate username and password
        username_error = auth.get_username_error(username)
        password_error = auth.get_password_error(password)

        if username_error or password_error is not None:
            flask.flash(username_error or password_error)
        elif repeat_password is None or repeat_password == "":
            flask.flash("Repeat your password!")
        elif password != repeat_password:
            flask.flash("Passwords did not match!")
        else:
            user = auth.try_sign_up(username, password)
            if user is None:
                flask.flash("Username was in use!")

        # Account created! Log the user in
        if user is None:
            return flask.render_template("signup.html", username=username)
        else:
            flask_login.login_user(user)
            return flask.redirect(flask.url_for("index"))

    else:
        return flask.render_template("signup.html")


@app.route("/logout")
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("index"))


# Handles Snippet Creation (Worked on by Alan Ly)
@app.route("/createSnippet", methods=["GET", "POST"])
@flask_login.login_required
def createSnippet():
    if flask.request.method == "POST":
        name = flask.request.form.get("name")
        code = flask.request.form.get("code")
        description = flask.request.form.get("description")
        tags = flask.request.form.get("tags")
        user_id = flask_login.current_user.id

        if not name or not code:
            flask.flash("Name and Code are required fields!")
            return flask.redirect(flask.url_for("createSnippet"))

        if tags is not None:
            tags = set(tags.replace(" ", "").split(","))

        data.create_snippet(name, code, user_id, description, tags)

        flask.flash("Snippet created successfully!")
        return flask.redirect(flask.url_for("snippets"))

    return flask.render_template("createSnippet.html")


# View All Personal User Snippets (Worked on by Alan Ly)
@app.route("/snippets")
@flask_login.login_required
def snippets():
    # Fetch all snippets for the logged-in user
    user_snippets = data.get_user_snippets(flask_login.current_user.id)
    return flask.render_template("snippets.html", snippets=user_snippets)


# View a Specific Snippet Page (Worked on by Alan Ly)
@app.route("/snippet/<int:snippet_id>")
@flask_login.login_required
def view_snippet(snippet_id):
    snippet = data.get_snippet(snippet_id)
    if snippet:
        return flask.render_template("snippetDetail.html", snippet=snippet)
    else:
        flask.flash("Snippet not found!")
        return flask.redirect(flask.url_for("snippets"))


@app.route("/search", methods=["GET"])
def search_snippets():
    query = request.args.get("q", "")  # Get the search query from the URL

    terms = query.split(" ")
    tags, names = set(), set()
    desc_has = []

    for term in terms:
        if term[0] == ":":
            tags.add(term[1:])
        elif term[0] == "-":
            desc_has.append(term[1:])
        else:
            names.add(term)

    results = data.search_snippets(names, tags, desc_has)

    return jsonify({"results": results})
