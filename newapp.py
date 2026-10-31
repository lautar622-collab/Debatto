# IMPORTS

import re
import uuid
import os
import random
from datetime import datetime
from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import getdb, init_app

load_dotenv()


# FLASK

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
init_app(app)


# UPLOAD CONFIG

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "uploads",
)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_IMAGE_SIZE_MB = 5

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_SIZE_MB * 1024 * 1024


# HELPERS

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_posts():
    db = getdb()

    posts = db.execute(
        """
        SELECT
            posts.id,
            posts.title,
            posts.content,
            posts.level,
            posts.language,
            posts.date,
            posts.userid,
            COALESCE(users.username, 'Anonymous') AS username
        FROM posts
        LEFT JOIN users ON posts.userid = users.id
        ORDER BY posts.date DESC
        """
    ).fetchall()

    result = []

    for post in posts:
        post = dict(post)

        topics = db.execute(
            """
            SELECT topics.name
            FROM topics
            JOIN post_topics ON topics.id = post_topics.topicid
            WHERE post_topics.postid = ?
            """,
            (post["id"],),
        ).fetchall()

        post["topics"] = [topic["name"] for topic in topics]

        media = db.execute(
            """
            SELECT id, mediatype, url, name
            FROM media
            WHERE postid = ?
            """,
            (post["id"],),
        ).fetchall()

        post["media"] = [dict(item) for item in media]
        result.append(post)

    return result


def build_response_tree(responses, parent_id=None):
    result = []

    for response in responses:
        if response["responseid"] == parent_id:
            item = dict(response)
            item["responses"] = build_response_tree(
                responses,
                response["id"],
            )
            result.append(item)

    return result

# POST

def get_post(post_id):
    db = getdb()

    post = db.execute(
        """
        SELECT
            posts.id,
            posts.title,
            posts.content,
            posts.level,
            posts.language,
            posts.date,
            posts.userid,
            COALESCE(users.username, 'Anonymous') AS username
        FROM posts
        LEFT JOIN users ON posts.userid = users.id
        WHERE posts.id = ?
        """,
        (post_id,),
    ).fetchone()

    if not post:
        return None

    post = dict(post)

    topics = db.execute(
        """
        SELECT topics.name
        FROM topics
        JOIN post_topics ON topics.id = post_topics.topicid
        WHERE post_topics.postid = ?
        """,
        (post_id,),
    ).fetchall()

    post["topics"] = [topic["name"] for topic in topics]

    responses = db.execute(
        """
        SELECT
            responses.id,
            responses.content,
            responses.type,
            responses.date,
            responses.userid,
            responses.responseid,
            responses.type,
            COALESCE(users.username, 'Anonymous') AS username
        FROM responses
        LEFT JOIN users ON responses.userid = users.id
        WHERE responses.postid = ?
        ORDER BY responses.date ASC
        """,
        (post_id,),
    ).fetchall()

    post["responses"] = build_response_tree(responses)

    media = db.execute(
        """
        SELECT id, mediatype, url, name
        FROM media
        WHERE postid = ?
        """,
        (post_id,),
    ).fetchall()

    post["media"] = [dict(item) for item in media]

    return post


# HOME

@app.route("/")
def index():
    posts = get_posts()
    random.shuffle(posts)

    return render_template("home.html", posts=posts)


# POST DETAIL AND RESPONSES

@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def post(post_id):
    db = getdb()

    if request.method == "POST":
        exists = db.execute(
            "SELECT id FROM posts WHERE id = ?",
            (post_id,),
        ).fetchone()

        if not exists:
            return "Post not found", 404

        content = request.form.get("rcontent", "").strip()
        response_type = request.form.get("rtype", "").strip()
        parent_id = request.form.get("parent_id", "").strip()

        if not content:
            return "Response content cannot be empty", 400

        if not response_type:
            return "Response Type Required", 400

        if parent_id:
            try:
                parent_id = int(parent_id)
            except ValueError:
                return "Invalid parent response", 400

            parent = db.execute(
                """
                SELECT id
                FROM responses
                WHERE id = ? AND postid = ?
                """,
                (parent_id, post_id),
            ).fetchone()

            if not parent:
                return "Parent response not found", 404
        else:
            parent_id = None

        db.execute(
            """
            INSERT INTO responses
                (content, type, date, userid, postid, responseid)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                content,
                response_type,
                datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S"),
                session.get("userid"),
                post_id,
                parent_id,
            ),
        )

        db.commit()

        return redirect(url_for("post", post_id=post_id))

    current_post = get_post(post_id)

    if not current_post:
        return "Post not found", 404

    return render_template("post.html", post=current_post)


# SIGNUP

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username", "").strip()
    rawpassword = request.form.get("password", "")
    email = request.form.get("email", "").strip()

    if len(username) < 3:
        return "Username too short", 400

    if len(rawpassword) < 5:
        return "Password too short", 400

    if len(username) > 25:
        return "Username too long", 400

    if len(rawpassword) > 30:
        return "Password too long", 400

    reserved = ["debatto", "anonymous"]

    if username.lower() in reserved:
        return "That username is reserved", 400

    db = getdb()

    existing_user = db.execute(
        "SELECT id FROM users WHERE lower(username) = lower(?)",
        (username,),
    ).fetchone()

    if existing_user:
        return "Username already exists", 409

    password = generate_password_hash(rawpassword)

    cursor = db.execute(
        """
        INSERT INTO users (username, password, email, joined)
        VALUES (?, ?, ?, ?)
        """,
        (
            username,
            password,
            email,
            datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S"),
        ),
    )

    db.commit()

    userid = cursor.lastrowid

    session["username"] = username
    session["userid"] = userid

    return redirect(url_for("index"))


# LOGIN

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    db = getdb()

    user = db.execute(
        "SELECT * FROM users WHERE lower(username) = lower(?)",
        (username,),
    ).fetchone()

    if not user:
        return "User not found", 404

    if not check_password_hash(user["password"], password):
        return "Incorrect password", 401

    session["username"] = user["username"]
    session["userid"] = user["id"]

    return redirect(url_for("index"))


# LOGOUT

@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("userid", None)

    return redirect(url_for("index"))


# CREATE POST

@app.route("/newpost", methods=["GET", "POST"])
def newpost():
    if request.method == "GET":
        return render_template("newpost.html")

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    level = request.form.get("level", "")

    if not title:
        return "Title is required", 400

    if not content:
        return "Content is required", 400

    if len(title) > 200:
        return "Title is too long", 400

    if level not in {"1", "2", "3", "4", "5"}:
        return "Invalid level", 400

    level = int(level)

    if len(content) > level * 2000:
        return "Content is too long", 400

    language = request.form.get("language", "gb")
    userid = session.get("userid")

    db = getdb()

    try:
        cursor = db.execute(
            """
            INSERT INTO posts
                (title, content, level, language, date, userid)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                content,
                level,
                language,
                datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S"),
                userid,
            ),
        )

        post_id = cursor.lastrowid

        for key in ["topic1", "topic2", "topic3"]:
            topic_name = request.form.get(key, "").strip().lower()

            if not topic_name:
                continue

            topic = db.execute(
                "SELECT id FROM topics WHERE name = ?",
                (topic_name,),
            ).fetchone()

            if topic:
                topic_id = topic["id"]
            else:
                cursor = db.execute(
                    "INSERT INTO topics (name) VALUES (?)",
                    (topic_name,),
                )
                topic_id = cursor.lastrowid

            db.execute(
                """
                INSERT OR IGNORE INTO post_topics (postid, topicid)
                VALUES (?, ?)
                """,
                (post_id, topic_id),
            )

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        images = request.files.getlist("images")

        for image in images:
            if not image or not image.filename:
                continue

            if not allowed_file(image.filename):
                continue

            ext = image.filename.rsplit(".", 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"

            save_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                unique_name,
            )

            image.save(save_path)

            url = f"/static/uploads/{unique_name}"

            db.execute(
                """
                INSERT INTO media (mediatype, url, name, postid)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "image",
                    url,
                    secure_filename(image.filename),
                    post_id,
                ),
            )

        db.commit()

    except Exception:
        db.rollback()

        app.logger.exception("Error al crear una publicación")

        return (
            "Error al crear la publicación. Revisá los logs de Render.",
            500,
        )

    return redirect(url_for("post", post_id=post_id))


# USER PROFILE

@app.route("/user/<username>")
def profile(username):
    db = getdb()

    user = db.execute(
        "SELECT * FROM users WHERE lower(username) = lower(?)",
        (username,),
    ).fetchone()

    if not user:
        return "User not found", 404

    posts = db.execute(
        """
        SELECT
            posts.id,
            posts.title,
            posts.content,
            posts.level,
            posts.language,
            posts.date,
            users.username
        FROM posts
        JOIN users ON posts.userid = users.id
        WHERE users.id = ?
        ORDER BY posts.id DESC
        """,
        (user["id"],),
    ).fetchall()

    user = dict(user)
    posts = [dict(item) for item in posts]

    return render_template("account.html", user=user, posts=posts)


# SEARCH

@app.route("/search")
def search():
    query = request.args.get("q", "").strip().lower()

    db = getdb()

    posts = db.execute(
        """
        SELECT
            posts.id,
            posts.title,
            posts.content,
            posts.level,
            posts.language,
            posts.date,
            COALESCE(users.username, 'Anonymous') AS username
        FROM posts
        LEFT JOIN users ON posts.userid = users.id
        WHERE lower(posts.title) LIKE ?
           OR lower(posts.content) LIKE ?
           OR lower(COALESCE(users.username, 'Anonymous')) LIKE ?
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%"),
    ).fetchall()

    result = []

    for post in posts:
        post = dict(post)

        topics = db.execute(
            """
            SELECT topics.name
            FROM topics
            JOIN post_topics ON topics.id = post_topics.topicid
            WHERE post_topics.postid = ?
            """,
            (post["id"],),
        ).fetchall()

        post["topics"] = [topic["name"] for topic in topics]
        result.append(post)

    return render_template("home.html", posts=result)


# LOCAL DEVELOPMENT

if __name__ == "__main__":
    app.run(debug=True)