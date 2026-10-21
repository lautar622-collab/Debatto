# IMPORTS #
import re
import json
import uuid
from db import getdb
from datetime import datetime
import os
import random
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
load_dotenv()
# FLASK #
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# UPLOAD CONFIG #
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_IMAGE_SIZE_MB = 5
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_SIZE_MB * 1024 * 1024

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
def get_posts():
    db = getdb()
    posts = db.execute("SELECT posts.id, posts.title, posts.content, posts.level, posts.language, posts.date, posts.userid, COALESCE(users.username, 'Anonymous') AS username FROM posts LEFT JOIN users ON posts.userid = users.id ORDER BY posts.date DESC").fetchall()
    result = []
    for post in posts:
        post = dict(post)
        topics = db.execute("SELECT topics.name FROM topics JOIN post_topics ON topics.id = post_topics.topicid WHERE post_topics.postid = ?", (post['id'],)).fetchall()
        post['topics'] = [topic['name'] for topic in topics]
        media=db.execute("SELECT id, mediatype, url, name FROM media WHERE postid = ?", (post["id"],)).fetchall()
        post["media"]=[dict(m) for m in media]
        result.append(post)
    db.close()
    return result
@app.route('/')
def index():
    posts = get_posts()
    random.shuffle(posts)
    return render_template('home.html', posts=posts)
def build_response_tree(responses, parent_id=None):
    result = []
    for response in responses:
        if response["responseid"]==parent_id:
            item=dict(response)
            item["responses"]=build_response_tree(responses, response["id"])
            result.append(item)
    return result
def get_post(post_id):
    db=getdb()
    post=db.execute("SELECT posts.id, posts.title, posts.content, posts.level, posts.language, posts.date, posts.userid, COALESCE(users.username, 'Anonymous') AS username FROM posts LEFT JOIN users ON posts.userid = users.id WHERE posts.id = ?", (post_id,)).fetchone()
    if not post:
        db.close()
        return None
    post=dict(post)
    topics=db.execute("SELECT topics.name FROM topics JOIN post_topics ON topics.id = post_topics.topicid WHERE post_topics.postid = ?", (post_id,)).fetchall()
    post["topics"]=[topic["name"] for topic in topics]
    responses=db.execute("SELECT responses.id, responses.content, responses.date, responses.userid, responses.responseid, COALESCE(users.username, 'Anonymous') AS username FROM responses LEFT JOIN users ON responses.userid = users.id WHERE responses.postid = ? ORDER BY responses.date ASC", (post_id,)).fetchall()
    post["responses"]=build_response_tree(responses)
    media=db.execute("SELECT id, mediatype, url, name FROM media WHERE postid = ?", (post_id,)).fetchall()
    post["media"]=[dict(m) for m in media]
    db.close()
    return post
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    db=getdb()
    current_post=db.execute("SELECT posts.id, posts.title, posts.content, posts.level, posts.language, posts.date, posts.userid, COALESCE(users.username, 'Anonymous') AS username FROM posts LEFT JOIN users ON posts.userid = users.id WHERE posts.id = ?", (post_id,)).fetchone()
    if not current_post:
        db.close()
        return "Post not found", 404
    if request.method=="POST":
        content=request.form.get("rcontent", "").strip()
        resposetype=request.form.get("rtype", "").strip()
        parent_id=request.form.get("parent_id")
        if not content:
            db.close()
            return "Response content cannot be empty", 400
        if not resposetype:
            db.close()
            return "Response Type Required", 400
        if parent_id:
            parent_id=int(parent_id)
        else:
            parent_id=None
        db.execute("INSERT INTO responses (content, type, date, userid, postid, responseid) VALUES (?, ?, ?, ?, ?, ?)", (content, resposetype, datetime.now().strftime("%A,%B,%d,%Y, %H:%M:%S"), session.get("userid"), post_id, parent_id))
        db.commit()
        db.close()
        return redirect(url_for("post", post_id=post_id))
    db.close()
    current_post=get_post(post_id)
    return render_template("post.html", post=current_post)
@app.route("/signup", methods=["POST"])
def signup():
    username=request.form.get("username","")
    rawpassword=request.form.get("password","")
    email=request.form.get("email","").strip()
    if len(username) < 3: return "Username too short"
    if len(rawpassword) < 5: return "Password too short"
    if len(username) > 25: return "Username too long"      
    if len(rawpassword) > 30: return "Password too long"
    reserved=["debatto", "anonymous"]
    if username.lower() in reserved: return "That username is reserved"
    db = getdb()
    existing_user = db.execute("SELECT id FROM users WHERE lower(username) = lower(?)", (username,)).fetchone()
    if existing_user:
        db.close()
        return "Username already exists"
    password = generate_password_hash(rawpassword)
    cursor = db.execute("INSERT INTO users (username, password, email, joined) VALUES (?,?,?,?)",(username,password,email,datetime.now().strftime("%A, %B, %d, %Y, %H:%M:%S")))
    db.commit()
    userid = cursor.lastrowid
    db.close()
    session["username"] = username
    session["userid"] = userid
    return redirect(url_for("index"))
@app.route("/login", methods=["POST"])
def login():
    username=request.form.get("username","")
    password=request.form.get("password","")
    db = getdb()
    user=db.execute("SELECT * FROM users WHERE lower(username) = lower(?)", (username,)).fetchone()
    db.close()
    if not user: return "User not found"
    if not check_password_hash(user["password"],password): return "Incorrect password"
    session["username"] = user["username"]
    session["userid"] = user["id"]
    return redirect(url_for("index"))
@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("userid", None)
    return redirect(url_for("index"))
@app.route("/newpost", methods=["GET","POST"])
def newpost():
    if request.method=="POST":
        print("DEBUG NEWPOST: recibí el formulario", flush=True)
        print("DEBUG NEWPOST: campos", list(request.form.keys()), flush=True)
        print("DEBUG NEWPOST: archivos", list(request.files.keys()), flush=True)
        title=request.form.get("title","").strip()
        content=request.form.get("content","")
        level=request.form.get("level","")
        if not title: return "Title is required",400
        if not content: return "Content is required",400
        if len(title) > 200: return "Title is too long",400
        if level not in {"1","2","3","4","5"}: return "Invalid level",400
        if len(content) > int(level) * 2000: return "Content is too long"
        level = int(level)
        language = request.form.get("language","gb")
        userid=session.get("userid")
        db = getdb()
        cursor = db.execute("INSERT INTO posts (title,content,level,language,date,userid) VALUES (?,?,?,?,?,?)", (title,content,level,language,datetime.now().strftime("%A,%B,%d,%Y, %H:%M:%S"),userid))
        post_id = cursor.lastrowid
        for key in ["topic1","topic2","topic3"]:
            topic_name=request.form.get(key,"").strip().lower()
            if not topic_name: continue
            topic=db.execute("SELECT id FROM topics WHERE name = ?", (topic_name,)).fetchone()
            if topic:
                topic_id = topic["id"]
            else:
                cursor = db.execute("INSERT INTO topics (name) VALUES (?)", (topic_name,))
                topic_id = cursor.lastrowid
            db.execute("INSERT OR IGNORE INTO post_topics (postid, topicid) VALUES (?,?)", (post_id,topic_id))
        images = request.files.getlist("images")
        for image in images:
            if image and image.filename and allowed_file(image.filename):
                ext = image.filename.rsplit(".", 1)[1].lower()
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                image.save(save_path)
                url = f"/static/uploads/{unique_name}"
                db.execute(
                    "INSERT INTO media (mediatype, url, name, postid) VALUES (?,?,?,?)",
                    ("image", url, secure_filename(image.filename), post_id)
                )
        video_url = request.form.get("video_url","").strip()
        if video_url:
            # Convert any YouTube URL to embed format
            import re
            yt_match = re.search(r'(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})', video_url)
            if yt_match:
                video_url = f"https://www.youtube.com/embed/{yt_match.group(1)}"
            db.execute("INSERT INTO media (mediatype, url, name, postid) VALUES (?,?,?,?)", ("video", video_url, "video", post_id))
        db.commit()
        db.close()
        return redirect(url_for("post", post_id=post_id))
    return render_template("newpost.html")
@app.route("/user/<username>")
def profile(username):
    db = getdb()
    user = db.execute("SELECT * FROM users WHERE lower(username) = lower(?)", (username,)).fetchone()
    if not user:
        db.close()
        return "User not found", 404
    posts=db.execute("SELECT posts.id, posts.title, posts.content, posts.level, posts.language, posts.date, users.username FROM posts JOIN users ON posts.userid = users.id WHERE users.id = ? ORDER BY posts.id DESC", (user["id"],)).fetchall()
    user = dict(user)
    posts = [dict(post) for post in posts]
    db.close()
    return render_template("account.html",user=user,posts=posts)
@app.route("/search")
def search():
    query = request.args.get("q","").strip().lower()
    db = getdb()
    posts = db.execute("SELECT posts.id, posts.title, posts.content, posts.level, posts.language, posts.date, COALESCE (users.username, 'Anonymous') AS username FROM posts LEFT JOIN users ON posts.userid = users.id WHERE lower(posts.title) LIKE ? OR lower(posts.content) LIKE ? OR lower(COALESCE(users.username, 'Anonymous')) LIKE ?",(f"%{query}%",f"%{query}%",f"%{query}%")).fetchall()
    result = []
    for post in posts:
        post = dict(post)
        topics = db.execute("SELECT topics.name FROM topics JOIN post_topics ON topics.id = post_topics.topicid WHERE post_topics.postid = ?",(post["id"],)).fetchall()
        post["topics"] = [
            topic["name"]
            for topic in topics
            ]
        result.append(post)
    db.close()
    return render_template("home.html",posts=result)

if __name__ == "__main__":app.run(debug=True)