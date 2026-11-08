# IMPORTS

import re
import uuid
import os
import random
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory,
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import getdb, init_app


# FLASK

app = Flask(__name__)

secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required.")

app.secret_key = secret_key
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(os.environ.get("RAILWAY_ENVIRONMENT_NAME"))

init_app(app)


# UPLOAD CONFIG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
UPLOAD_FOLDER = os.path.abspath(
    os.environ.get("UPLOAD_FOLDER", DEFAULT_UPLOAD_FOLDER)
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


# PERSISTENT UPLOADS
# Keep the old URL working for media records created before this deployment.

@app.route("/uploads/<path:filename>")
@app.route("/static/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


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

            image_url = url_for("uploaded_file", filename=unique_name)

            db.execute(
                """
                INSERT INTO media (mediatype, url, name, postid)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "image",
                    image_url,
                    secure_filename(image.filename),
                    post_id,
                ),
            )

        db.commit()

    except Exception:
        db.rollback()

        app.logger.exception("Error al crear una publicación")

        return (
            "Error al crear la publicación. Revisá los logs del servicio.",
            500,
        )

    return redirect(url_for("post", post_id=post_id))


# REPORTING AND MODERATION

def current_user_is_admin():
    userid = session.get("userid")
    if not userid:
        return False
    user = getdb().execute(
        "SELECT role FROM users WHERE id = ?", (userid,)
    ).fetchone()
    return bool(user and user["role"] == "Admin")


@app.route("/report/<content_type>/<int:target_id>", methods=["POST"])
def report_content(content_type, target_id):
    userid = session.get("userid")
    if not userid:
        return redirect(url_for("index"))

    if content_type not in {"post", "response"}:
        return "Invalid report target", 400

    db = getdb()
    if content_type == "post":
        target = db.execute(
            "SELECT id FROM posts WHERE id = ?", (target_id,)
        ).fetchone()
        post_id = target_id
    else:
        target = db.execute(
            "SELECT id, postid FROM responses WHERE id = ?", (target_id,)
        ).fetchone()
        post_id = target["postid"] if target else None

    if not target:
        return "Content not found", 404

    existing = db.execute(
        """
        SELECT id FROM content_reports
        WHERE content_type = ? AND target_id = ? AND userid = ?
        """,
        (content_type, target_id, userid),
    ).fetchone()

    if not existing:
        db.execute(
            """
            INSERT INTO content_reports
                (content_type, target_id, userid, date)
            VALUES (?, ?, ?, ?)
            """,
            (
                content_type,
                target_id,
                userid,
                datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S"),
            ),
        )
        db.commit()

    if content_type == "post":
        return redirect(url_for("index"))
    return redirect(url_for("post", post_id=post_id))


@app.route("/mossy-lantern-4821")
def hidden_review_queue():
    if not current_user_is_admin():
        return "Not found", 404

    db = getdb()
    reports = db.execute(
        """
        SELECT
            cr.content_type,
            cr.target_id,
            MAX(cr.date) AS last_reported,
            COUNT(cr.id) AS report_count,
            CASE WHEN cr.content_type = 'post' THEN p.content ELSE r.content END AS content,
            CASE WHEN cr.content_type = 'post' THEN p.title ELSE parent.title END AS post_title,
            CASE WHEN cr.content_type = 'post' THEN p.id ELSE parent.id END AS post_id,
            CASE WHEN cr.content_type = 'post' THEN p.userid ELSE r.userid END AS author_id,
            COALESCE(author.username, 'Anonymous') AS author
        FROM content_reports cr
        LEFT JOIN posts p
            ON cr.content_type = 'post' AND p.id = cr.target_id
        LEFT JOIN responses r
            ON cr.content_type = 'response' AND r.id = cr.target_id
        LEFT JOIN posts parent
            ON parent.id = r.postid
        LEFT JOIN users author
            ON author.id = CASE
                WHEN cr.content_type = 'post' THEN p.userid
                ELSE r.userid
            END
        GROUP BY cr.content_type, cr.target_id
        ORDER BY last_reported DESC
        """
    ).fetchall()

    return render_template("reports.html", reports=reports)


@app.route("/mossy-lantern-4821/delete/<content_type>/<int:target_id>", methods=["POST"])
def moderation_delete(content_type, target_id):
    if not current_user_is_admin():
        return "Not found", 404

    action = request.form.get("action")
    db = getdb()

    if action == "account":
        if content_type == "post":
            owner = db.execute(
                "SELECT userid FROM posts WHERE id = ?", (target_id,)
            ).fetchone()
        elif content_type == "response":
            owner = db.execute(
                "SELECT userid FROM responses WHERE id = ?", (target_id,)
            ).fetchone()
        else:
            return "Invalid target", 400

        if not owner or owner["userid"] is None:
            return "Account not found", 404

        account_id = owner["userid"]
        db.execute(
            """
            WITH RECURSIVE tree(id) AS (
                SELECT id FROM responses
                WHERE userid = ? OR postid IN (SELECT id FROM posts WHERE userid = ?)
                UNION
                SELECT child.id FROM responses child
                JOIN tree parent ON child.responseid = parent.id
            )
            DELETE FROM content_reports
            WHERE (content_type = 'response' AND target_id IN (SELECT id FROM tree))
               OR (content_type = 'post' AND target_id IN (SELECT id FROM posts WHERE userid = ?))
               OR userid = ?
            """,
            (account_id, account_id, account_id, account_id),
        )
        db.execute(
            """
            WITH RECURSIVE tree(id) AS (
                SELECT id FROM responses
                WHERE userid = ? OR postid IN (SELECT id FROM posts WHERE userid = ?)
                UNION
                SELECT child.id FROM responses child
                JOIN tree parent ON child.responseid = parent.id
            )
            DELETE FROM responses WHERE id IN (SELECT id FROM tree)
            """,
            (account_id, account_id),
        )
        db.execute("DELETE FROM media WHERE postid IN (SELECT id FROM posts WHERE userid = ?)", (account_id,))
        db.execute("DELETE FROM post_topics WHERE postid IN (SELECT id FROM posts WHERE userid = ?)", (account_id,))
        db.execute("DELETE FROM postversion WHERE userid = ? OR postid IN (SELECT id FROM posts WHERE userid = ?)", (account_id, account_id))
        db.execute("DELETE FROM posts WHERE userid = ?", (account_id,))
        db.execute("DELETE FROM content_reports WHERE userid = ?", (account_id,))
        db.execute("DELETE FROM users WHERE id = ?", (account_id,))
    elif action == "content" and content_type == "post":
        exists = db.execute("SELECT id FROM posts WHERE id = ?", (target_id,)).fetchone()
        if not exists:
            return "Post not found", 404
        db.execute("DELETE FROM content_reports WHERE (content_type = 'post' AND target_id = ?) OR (content_type = 'response' AND target_id IN (SELECT id FROM responses WHERE postid = ?))", (target_id, target_id))
        db.execute("DELETE FROM media WHERE postid = ?", (target_id,))
        db.execute("DELETE FROM post_topics WHERE postid = ?", (target_id,))
        db.execute("DELETE FROM postversion WHERE postid = ?", (target_id,))
        db.execute("DELETE FROM responses WHERE postid = ?", (target_id,))
        db.execute("DELETE FROM posts WHERE id = ?", (target_id,))
    elif action == "content" and content_type == "response":
        exists = db.execute("SELECT id FROM responses WHERE id = ?", (target_id,)).fetchone()
        if not exists:
            return "Response not found", 404
        db.execute(
            """
            WITH RECURSIVE tree(id) AS (
                SELECT id FROM responses WHERE id = ?
                UNION
                SELECT child.id FROM responses child
                JOIN tree parent ON child.responseid = parent.id
            )
            DELETE FROM content_reports WHERE content_type = 'response'
            AND target_id IN (SELECT id FROM tree)
            """,
            (target_id,),
        )
        db.execute(
            """
            WITH RECURSIVE tree(id) AS (
                SELECT id FROM responses WHERE id = ?
                UNION
                SELECT child.id FROM responses child
                JOIN tree parent ON child.responseid = parent.id
            )
            DELETE FROM responses WHERE id IN (SELECT id FROM tree)
            """,
            (target_id,),
        )
    else:
        return "Invalid moderation action", 400

    db.commit()
    return redirect(url_for("hidden_review_queue"))


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
