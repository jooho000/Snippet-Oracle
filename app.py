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
import auth
import uuid
import os
import base64
import data
from io import BytesIO
from PIL import Image
from flask import jsonify, request, g
from urllib.parse import urlparse


app = flask.Flask("snippet_oracle")
auth.init(app, "login")
app.secret_key = auth.get_secret_key()
data.preload_transformer()


# Configure file upload settings
UPLOAD_FOLDER = "static/profile_pictures"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limit file size to 16 MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.cli.command("reset-db")
def reset_db():
    get_db().reset()


@app.cli.command("populate-db")
def populate_db():
    get_db().reset()
    get_db().populate()


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = data.Data()
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    """
    Render the homepage with the list of snippets.
    """
    user_snippets = []
    user_data = None

    if flask_login.current_user.is_authenticated:
        user_snippets = get_db().get_user_snippets(
            flask_login.current_user.id, flask_login.current_user.id
        )
        user_data = get_db().get_user_details(flask_login.current_user.id)
    return flask.render_template("index.html", snippets=user_snippets, user=user_data)


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
    cur = get_db()._db.cursor()

    if flask.request.method == "POST":
        bio = flask.request.form.get("bio", "")
        links = flask.request.form.getlist("links")
        profile_picture_base64 = flask.request.form.get("profile_picture_base64")

        # Handle base64-encoded image
        if profile_picture_base64:
            # Extract the image content from base64 string
            header, encoded_image = profile_picture_base64.split(",", 1)
            image_data = base64.b64decode(encoded_image)
            image = Image.open(BytesIO(image_data))

            if image.size[0] > 1024 or image.size[1] > 1024:
                flask.flash("Cropped image is too large! Max allowed size is 1024x1024 pixels.", "warning")
                return flask.redirect(flask.request.url)

            # Generate a unique filename
            file_extension = profile_picture_base64.split("/")[1].split(";")[0]
            unique_filename = str(uuid.uuid4()) + "." + file_extension
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)

            # Save the image to the filesystem
            image.save(file_path)

            # Remove old profile picture if exists
            cur.execute(
                "SELECT ProfilePicture FROM User WHERE ID = ?",
                [flask_login.current_user.id],
            )
            old_profile_picture = cur.fetchone()[0]
            if old_profile_picture:
                old_image_path = os.path.join(
                    app.config["UPLOAD_FOLDER"], old_profile_picture
                )
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

            # Update the user's profile picture in the database
            cur.execute(
                """
                UPDATE User
                SET ProfilePicture = ?
                WHERE ID = ?
            """,
                [unique_filename, flask_login.current_user.id],
            )

        # Update the user's bio
        cur.execute(
            """
            UPDATE User
            SET Bio = ?
            WHERE ID = ?
        """,
            [bio, flask_login.current_user.id],
        )

        # Clear existing links and insert updated links
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

        get_db()._db.commit()
        flask.flash("Profile updated successfully!", "info")

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
    user_snippets = get_db().get_user_snippets(
        flask_login.current_user.id, flask_login.current_user.id
    )
    user_details = get_db().get_user_details(flask_login.current_user.id)

    return flask.render_template(
        "profile.html",
        user=user_details,
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
    return "/static/profile_pictures/default_image.png"


@app.route("/createSnippet", methods=["GET", "POST"])
@app.route("/remixSnippet/<int:snippet_id>", methods=["GET", "POST"])
@flask_login.login_required
def createSnippet(snippet_id=None):
    """Handles both creating new snippets and remixing existing ones."""

    # Fetch original snippet if remixing
    original_snippet = None
    if snippet_id:
        original_snippet = get_db().get_snippet(snippet_id, flask_login.current_user.id)
        if not original_snippet:
            flask.flash("Original snippet not found or inaccessible!", "danger")
            return flask.redirect(flask.url_for("snippets"))

    if flask.request.method == "POST":
        name = flask.request.form.get("name")
        code = flask.request.form.get("code")
        description = flask.request.form.get("description", "")
        tags = flask.request.form.get("tags", "")
        is_public = flask.request.form.get("is_public") == "1"
        user_id = flask_login.current_user.id

        try:
            permitted_users = flask.request.form.getlist("permitted_users[]")
            permitted_users = [int(uid) for uid in permitted_users if uid.isdigit()]
        except (ValueError, TypeError) as e:
            print(f"Error parsing permitted_users: {e}")
            permitted_users = []

        if not is_public:
            permitted_users.append(user_id)  # Ensure owner has permission

        if not name or not code:
            flask.flash("Name and Code are required fields!", "warning")
            return flask.redirect(flask.url_for("createSnippet", snippet_id=snippet_id))

        if tags:
            tags = set(tags.replace(" ", "").split(","))

        new_snippet_id = get_db().create_snippet(
            name,
            code,
            user_id,
            description,
            tags,
            is_public,
            permitted_users,
            parent_snippet_id=snippet_id,  # Set parent snippet if remixing
        )

        if new_snippet_id:
            flask.flash("Snippet created successfully!", "success")
            return flask.redirect(flask.url_for("snippets"))
        else:
            flask.flash("Failed to create snippet!", "danger")

    all_users = get_db().get_all_users_excluding_current(flask_login.current_user.id)

    return flask.render_template(
        "createSnippet.html",
        all_users=all_users,
        preset_tags=data.preset_tags,
        snippet=original_snippet,  # Pass original snippet if remixing
        user=get_db().get_user_details(flask_login.current_user.id),
    )


# View All Personal User Snippets (Worked on by Alan Ly)
@app.route("/snippets")
@flask_login.login_required
def snippets():
    # Fetch all snippets for the logged-in user
    user_snippets = get_db().get_user_snippets(
        flask_login.current_user.id, flask_login.current_user.id
    )
    user_details = get_db().get_user_details(flask_login.current_user.id)
    return flask.render_template(
        "snippets.html", user=user_details, snippets=user_snippets
    )


@app.route("/snippet/<int:snippet_id>", methods=["GET"])
def view_snippet(snippet_id):
    current_user_id = auth.get_current_id_or_none()
    snippet = get_db().get_snippet(snippet_id, current_user_id)
    if not snippet:
        flask.flash("Snippet not found or not accessible!", "warning")
        return flask.redirect(flask.url_for("snippets"))

    parent_snippet = None
    if snippet["parent_snippet_id"] is not None:
        parent_snippet = get_db().get_snippet(
            snippet["parent_snippet_id"], current_user_id
        )

    comments = get_db().get_comments(snippet_id)  # Fetch comments from database

    return flask.render_template(
        "snippetDetail.html",
        user=get_db().get_user_details(current_user_id),
        snippet=snippet,
        comments=comments,
        parent_snippet=parent_snippet,
    )


# Allows users to toggle snippet visibility (Public/Private)
@app.route("/snippet/<int:snippet_id>/visibility", methods=["POST"])
@flask_login.login_required
def update_snippet_visibility(snippet_id):
    is_public = request.form.get("is_public")

    snippet = get_db().get_snippet(snippet_id)
    if not snippet or str(snippet["user_id"]) != flask_login.current_user.id:
        flask.flash("Unauthorized or snippet not found!", "danger")
        return flask.redirect(flask.url_for("snippets"))

    get_db().set_snippet_visibility(snippet_id, is_public)
    flask.flash("Snippet visibility updated!", "success")

    return flask.redirect(flask.url_for("view_snippet", snippet_id=snippet_id))


# Allow users to access private snippets via shareable links
@app.route("/share/<string:link>")
def view_snippet_by_link(link):
    snippet_id = get_db().get_snippet_id_by_shareable_link(link)
    if snippet_id is not None:
        user_id = (
            flask_login.current_user.id
            if flask_login.current_user.is_authenticated
            else None
        )
        snippet = get_db().get_snippet(snippet_id, user_id)
        return flask.render_template(
            "snippetDetail.html",
            user=get_db().get_user_details(flask_login.current_user.id),
            snippet=snippet,
        )
    else:
        flask.flash("Invalid or expired link!", "warning")
        return flask.redirect(flask.url_for("index"))


@app.route("/search/", methods=["GET"])
def search_snippets():
    query = request.args.get("q", "")  # Get the search query from the URL
    public = True if request.headers.get("Search-Type") == "true" else False
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
        results = get_db().search_snippets(names, tags, desc_has, user_id, public)
    else:
        results = get_db().smart_search_snippets(query, user_id, public)

    return jsonify({"results": results})


@app.route("/editSnippet/<int:snippet_id>", methods=["GET", "POST"])
@flask_login.login_required
def edit_snippet(snippet_id):
    current_user_id = flask_login.current_user.id  # Get the current user's ID
    snippet = get_db().get_snippet(snippet_id, current_user_id)
    prev_users = get_db().get_all_users_with_permission(snippet_id, current_user_id)

    if not snippet or str(snippet["user_id"]) != flask_login.current_user.id:
        flask.flash("Unauthorized or snippet not found!", "danger")
        return flask.redirect(flask.url_for("snippets"))

    if flask.request.method == "POST":
        name = flask.request.form.get("name")
        code = flask.request.form.get("code")
        description = flask.request.form.get("description")
        tags = flask.request.form.get("tags")
        user_id = flask_login.current_user.id
        print("HELLO IS IT PUBLIC: " + str(flask.request.form.get("is_public") == "1"))
        is_public = flask.request.form.get("is_public") == "1"
        print("STORED VALUE IS: " + str(is_public))
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
            permitted_users.append(int(user_id))
            permitted_users = set(permitted_users)

        if not name or not code:
            flask.flash("Name and Code are required fields!", "warning")
            return flask.redirect(flask.url_for("createSnippet"))

        if tags is not None:
            tags = set(tags.replace(" ", "").split(","))

        get_db().update_snippet(
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
        return flask.redirect(
            flask.url_for(
                "view_snippet",
                user=get_db().get_user_details(flask_login.current_user.id),
                snippet_id=snippet_id,
            )
        )
    elif snippet:
        all_users = get_db().get_all_users_excluding_current(
            flask_login.current_user.id
        )
        return flask.render_template(
            "editSnippet.html",
            user=get_db().get_user_details(flask_login.current_user.id),
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
    snippet = get_db().get_snippet(snippet_id, current_user_id)
    if not snippet or str(snippet["user_id"]) != flask_login.current_user.id:
        flask.flash("Unauthorized or snippet not found!", "danger")
        return flask.redirect(flask.url_for("snippets"))
    get_db().delete_snippet(snippet_id, snippet["user_id"])
    return flask.redirect(flask.url_for("snippets"))


@app.route("/snippet/<int:snippet_id>/comment", methods=["POST"])
@flask_login.login_required
def add_comment(snippet_id):
    comment_content = flask.request.form.get("comment")
    parent_id = flask.request.form.get("parent_id")  # Get Parent Comment ID

    if not comment_content.strip():
        flask.flash("Comment cannot be empty!", "warning")
        return flask.redirect(flask.url_for("view_snippet", snippet_id=snippet_id))

    user_id = flask_login.current_user.id
    get_db().add_comment(snippet_id, user_id, comment_content, parent_id)
    flask.flash("Comment added successfully!", "success")

    return flask.redirect(flask.url_for("view_snippet", snippet_id=snippet_id))


@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
@flask_login.login_required
def delete_comment(comment_id):
    """Deletes a comment and its replies if the current user is the author."""
    current_user_id = flask_login.current_user.id

    # Get the comment details
    comment = get_db().get_comment_by_id(comment_id)

    # Get the snippet details to get snippet author
    snippet = get_db().get_snippet(comment["snippet_id"])

    # Checks if the current user is the comment/snippet author
    if comment["user_id"] != int(current_user_id) and snippet["user_id"] != int(
        current_user_id
    ):
        flask.flash("Unauthorized User!", "danger")
        return flask.redirect(flask.url_for("index"))

    # Delete the comment and its replies
    get_db().delete_comment(comment_id)
    flask.flash("Comment and its replies deleted successfully!", "success")

    return flask.redirect(
        flask.url_for("view_snippet", snippet_id=comment["snippet_id"])
    )


@app.route("/likes/<int:snippet_id>", methods=["POST"])
@flask_login.login_required
def add_like(snippet_id):
    """Adds a like to a snippet for the current user."""
    get_db().add_like(snippet_id, flask_login.current_user.id)
    likes = get_db().get_likes(snippet_id)
    return jsonify({likes: likes})


@app.route("/likes/<int:snippet_id>", methods=["DELETE"])
@flask_login.login_required
def remove_like(snippet_id):
    """Removes the current user's like from a snippet."""
    get_db().remove_like(snippet_id, flask_login.current_user.id)
    likes = get_db().get_likes(snippet_id)
    return jsonify({likes: likes})
