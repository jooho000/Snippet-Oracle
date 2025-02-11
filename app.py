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
import uuid
import json
from flask import jsonify, request
from urllib.parse import urlparse


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
    """
    Render the homepage with the list of snippets.
    """
    user_snippets = []
    if flask_login.current_user.is_authenticated:
        user_snippets = data.get_user_snippets(flask_login.current_user.id)
    return flask.render_template("index.html", snippets=user_snippets)


@app.route("/login", methods=["GET", "POST"])
def login():
    if flask.request.method == "POST":
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")

        user = auth.try_login(username, password)

        if username is None or username == "":
            flask.flash("Input a username!", "warning")
        elif password is None or password == "":
            flask.flash("Input a password!", "warning")
        elif user is None:
            flask.flash("Invalid username or password!", "warning")

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
            flask.flash(username_error or password_error, "warning")
        elif repeat_password is None or repeat_password == "":
            flask.flash("Repeat your password!", "warning")
        elif password != repeat_password:
            flask.flash("Passwords did not match!", "warning")
        else:
            user = auth.try_sign_up(username, password)
            if user is None:
                flask.flash("Username was in use!", "warning")

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


# Add Route for Profile Page
@app.route("/profile", methods=["GET", "POST"])
@flask_login.login_required
def profile():
    cur = data._db.cursor()

    if flask.request.method == "POST":
        # Handle Any Profile Edits
        bio = flask.request.form.get("bio", "")
        profile_picture = flask.request.form.get("profile_picture", "")
        links = flask.request.form.getlist("links")
        print(f"Received Profile Picture URL: {profile_picture}")
        # Update user bio and profile picture
        cur.execute(
            """
            UPDATE User
            SET Bio = ?, ProfilePicture = ?
            WHERE ID = ?
            """,
            [bio, profile_picture, flask_login.current_user.id],
        )
        print(
            f"Updated Profile Picture for User ID {flask_login.current_user.id} with URL: {profile_picture}"
        )

        # Clear any existing links and insert updated links
        cur.execute("DELETE FROM Links WHERE UserID = ?", [flask_login.current_user.id])
        for link in links:
            if link.strip():
                cur.execute(
                    """
                    INSERT INTO Links (UserID, Platform, URL)
                    VALUES (?, ?, ?)
                    """,
                    [flask_login.current_user.id, "Custom", link],
                )

        data._db.commit()
        flask.flash("Profile updated successfully!", "info")

    # Fetch user details and links
    cur.execute(
        "SELECT Name, Bio, ProfilePicture FROM User WHERE ID = ?",
        [flask_login.current_user.id],
    )
    user = cur.fetchone()

    profile_picture = user[2] if user[2] else ""

    cur.execute(
        "SELECT Platform, URL FROM Links WHERE UserID = ?",
        [flask_login.current_user.id],
    )
    user_links = cur.fetchall()

    # Fetch Snippets with Pagination
    page = int(flask.request.args.get("page", 1))
    limit = 10
    offset = (page - 1) * limit
    cur.execute(
        """
        SELECT ID, Name, Description FROM Snippet
        WHERE UserID = ? ORDER BY Date DESC LIMIT ? OFFSET ?
        """,
        [flask_login.current_user.id, limit, offset],
    )
    user_snippets = data.get_user_snippets(flask_login.current_user.id)

    return flask.render_template(
        "profile.html",
        user=user,
        links=user_links,
        snippets=user_snippets,
        page=page,
        get_social_icon=get_social_icon,
    )


# Helper function to get social media platform icon
def get_social_icon(url):
    # Mapping for common social platforms
    icon_map = {
        "github.com": "/static/icons/github.png",
        "x.com": "/static/icons/x.png",
        "discord.com": "/static/icons/discord.png",
        "linkedin.com": "/static/icons/linkedin.png",
        "facebook.com": "/static/icons/facebook.png",
        "instagram.com": "/static/icons/instagram.png",
        "youtube.com": "/static/icons/youtube.png",
    }

    # Check the domain of the URL to match with social platforms
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    for platform, icon_url in icon_map.items():
        if platform in domain:
            return icon_url

    # Default icon if no platform match
    return "/static/icons/default_image.png"


@app.route("/createSnippet", methods=["GET", "POST"])
@flask_login.login_required
def createSnippet():

    if flask.request.method == "POST":
        name = flask.request.form.get("name")
        code = flask.request.form.get("code")
        description = flask.request.form.get("description", "")
        tags = flask.request.form.get("tags", "")
        is_public = flask.request.form.get("is_public") == "1"
        user_id = flask_login.current_user.id

        try:
            permitted_users = flask.request.form.getlist(
                "permitted_users[]"
            )  # Ensure the correct key
            permitted_users = [
                int(user_id) for user_id in permitted_users if user_id.isdigit()
            ]  # Convert to integers
        except (ValueError, TypeError) as e:
            print(f"Error parsing permitted_users: {e}")
            permitted_users = []

        if not is_public:
            permitted_users.append(user_id)

        if not name or not code:
            flask.flash("Name and Code are required fields!", "warning")
            return flask.redirect(flask.url_for("createSnippet"))

        if tags:
            tags = set(tags.replace(" ", "").split(","))

        snippet_id = data.create_snippet(
            name, code, user_id, description, tags, is_public, permitted_users
        )

        if snippet_id:
            flask.flash("Snippet created successfully!", "success")
            return flask.redirect(flask.url_for("snippets"))
        else:
            flask.flash("Failed to create snippet!", "danger")

    all_users = data.get_all_users_excluding_current(flask_login.current_user.id)
    return flask.render_template(
        "createSnippet.html", all_users=all_users, preset_tags=data.preset_tags
    )


# View All Personal User Snippets (Worked on by Alan Ly)
@app.route("/snippets")
@flask_login.login_required
def snippets():
    # Fetch all snippets for the logged-in user
    user_snippets = data.get_user_snippets(flask_login.current_user.id)
    return flask.render_template("snippets.html", snippets=user_snippets)


# View a Specific Snippet Page (Worked on by Alan Ly)
@app.route("/snippet/<int:snippet_id>", methods=["GET"])
@flask_login.login_required
def view_snippet(snippet_id):
    current_user_id = flask_login.current_user.id  # Get the current user's ID
    snippet = data.get_snippet(
        snippet_id, current_user_id
    )  # Pass the user ID to get_snippet
    if not snippet:
        flask.flash("Snippet not found or not accessible!", "warning")
        return flask.redirect(flask.url_for("snippets"))

    return flask.render_template("snippetDetail.html", snippet=snippet)


# Allows users to toggle snippet visibility (Public/Private)
@app.route("/snippet/<int:snippet_id>/visibility", methods=["POST"])
@flask_login.login_required
def update_snippet_visibility(snippet_id):
    is_public = request.form.get("is_public")

    snippet = data.get_snippet(snippet_id)
    if not snippet or str(snippet["user_id"]) != flask_login.current_user.id:
        flask.flash("Unauthorized or snippet not found!", "danger")
        return flask.redirect(flask.url_for("snippets"))

    data.set_snippet_visibility(snippet_id, is_public)
    flask.flash("Snippet visibility updated!", "success")

    return flask.redirect(flask.url_for("view_snippet", snippet_id=snippet_id))


# Allow users to access private snippets via shareable links
@app.route("/share/<string:link>")
def view_snippet_by_link(link):
    snippet = data.get_snippet_by_shareable_link(link)
    if snippet:
        return flask.render_template("snippetDetail.html", snippet=snippet)
    else:
        flask.flash("Invalid or expired link!", "warning")
        return flask.redirect(flask.url_for("index"))


@app.route("/search", methods=["GET"])
def search_snippets():
    query = request.args.get("q", "")  # Get the search query from the URL
    if len(query) > 300:
        query = query[:300]

    terms = query.split(" ")
    tags, names = set(), set()
    desc_has = []

    for term in terms:
        if term != "":
            if term[0] == ":":
                tags.add(term[1:])
            elif term[0] == "-":
                desc_has.append(term[1:])
            else:
                names.add(term)

    user_id = None
    if flask_login.current_user.is_authenticated:
        user_id = flask_login.current_user.id

    if len(tags) or len(desc_has) > 0:
        results = data.search_snippets(names, tags, desc_has, user_id)
    else:
        results = data.smart_search_snippets(query, user_id)

    return jsonify({"results": results})


@app.route("/editSnippet/<int:snippet_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_snippet(snippet_id):
    current_user_id = flask_login.current_user.id  # Get the current user's ID
    snippet = data.get_snippet(snippet_id, current_user_id)
    prev_users = data.get_all_users_with_permission(snippet_id)

    if not snippet or str(snippet["user_id"]) != flask_login.current_user.id:
        flask.flash("Unauthorized or snippet not found!", "danger")
        return flask.redirect(flask.url_for("snippets"))

    if flask.request.method == "POST":
        name = flask.request.form.get("name")
        code = flask.request.form.get("code")
        description = flask.request.form.get("description")
        tags = flask.request.form.get("tags")
        user_id = flask_login.current_user.id
        is_public = flask.request.form.get("is_public") == "1"

        try:
            permitted_users = flask.request.form.getlist(
                "permitted_users[]"
            )  # Ensure the correct key
            permitted_users = [
                int(user_id) for user_id in permitted_users if user_id.isdigit()
            ]  # Convert to integers
            prev_permissions = set([int(user_id["id"]) for user_id in prev_users])
        except (ValueError, TypeError) as e:
            print(f"Error parsing permitted_users: {e}")
            permitted_users = []

        if not is_public:
            permitted_users.append(int(user_id))
            permitted_users = set(permitted_users)

        if not name or not code:
            flask.flash("Name and Code are required fields!", "warning")
            return flask.redirect(flask.url_for("createSnippet"))

        if tags is not None:
            tags = set(tags.replace(" ", "").split(","))

        data.update_snippet(
            snippet_id,
            user_id,
            name,
            code,
            description,
            tags,
            is_public,
            permitted_users,
        )

        flask.flash("Snippet Edited successfully!")
        return flask.redirect(flask.url_for("view_snippet", snippet_id=snippet_id))
    elif snippet:
        all_users = data.get_all_users_excluding_current(flask_login.current_user.id)
        return flask.render_template(
            "editSnippet.html",
            all_users=all_users,
            snippet=snippet,
            tags=snippet["tags"],
            users=prev_users,
            preset_tags=data.preset_tags,
        )
    else:
        flask.flash("Snippet not found!", "warning")
        return flask.redirect(flask.url_for("snippets"))


@app.route("/deleteSnippet/<int:snippet_id>")
def delete_Snippet(snippet_id):
    current_user_id = flask_login.current_user.id  # Get the current user's ID
    snippet = data.get_snippet(snippet_id, current_user_id)
    if not snippet or str(snippet["user_id"]) != flask_login.current_user.id:
        flask.flash("Unauthorized or snippet not found!", "danger")
        return flask.redirect(flask.url_for("snippets"))
    data.delete_snippet(snippet_id, snippet["user_id"])
    return flask.redirect(flask.url_for("snippets"))
