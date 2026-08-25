from datetime import datetime
date=datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S")
import json
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key: raise ValueError("No SECRET_KEY set for Flask application. Please set it in the .env file.")
def find_response(responses, response_id):
    for response in responses:
        if response["id"] == response_id:return response
        found = find_response(response["responses"], response_id)
        if found:return found
    return None
@app.route("/")
def index():
    with open("posts.json", "r") as file:posts = json.load(file)
    random.shuffle(posts)
    return render_template("home.html", posts=posts)
@app.route("/newpost", methods=["GET", "POST"])
def newpost():
    if request.method == "POST":
        with open("posts.json", "r") as file:posts = json.load(file)
        if posts:new_id = max(post["id"] for post in posts) + 1
        else:new_id = 1
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        level = request.form.get("level", "").strip()
        if not title:return "Title is required.", 400
        if not content:return "Content is required.", 400
        if len(title) > 200:return "Title is too long.", 400
        if len(content) > 5000:return "Content is too long.", 400
        if not level:return "Level is required.", 400
        if level not in {"1", "2", "3", "4", "5"}:return "Invalid level.", 400
        level = int(level)
        topic1 = ""
        topic2 = ""
        topic3 = ""
        if len(request.form.get("topic1", "").strip().lower().replace(" ", "-")) > 0:topic1 = request.form.get("topic1", "").strip().lower().replace(" ", "-")
        if len(request.form.get("topic2", "").strip().lower().replace(" ", "-")) > 0:topic2 = request.form.get("topic2", "").strip().lower().replace(" ", "-")
        if len(request.form.get("topic3", "").strip().lower().replace(" ", "-")) > 0:topic3 = request.form.get("topic3", "").strip().lower().replace(" ", "-")
        post = {
            "title": title,
            "content": content,
            "level": level,
            "id": new_id,
            "date": datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S"),
            "username": session.get("username", "Anonymous"),
            "topics": [topic1, topic2, topic3],
            "responses": []
        }
        posts.append(post)
        with open("posts.json", "w") as file:json.dump(posts, file, indent=4)
        return redirect(url_for("index"))
    return render_template("newpost.html")
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def post(post_id):
    with open("posts.json", "r") as file:
        posts = json.load(file)
    for p in posts:
        if p["id"] == post_id:
            if request.method == "POST":
                content = request.form["rcontent"]
                response_type = request.form["rtype"]
                parent_id = request.form.get("parent_id")
                if parent_id:parent = find_response(p["responses"], parent_id)
                else:parent = None
                if parent:
                    new_id = f"{parent_id}.{len(parent['responses']) + 1}"
                    parent["responses"].append({
                        "id": new_id,
                        "content": content,
                        "type": response_type,
                        "username": session.get("username", "Anonymous"),
                        "date": datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S"),
                        "responses": []
                    })

                else:
                    new_id = f"{post_id}.{len(p['responses']) + 1}"
                    p["responses"].append({
                        "id": new_id,
                        "content": content,
                        "type": response_type,
                        "username": session.get("username", "Anonymous"),
                        "date": datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S"),
                        "responses": []
                    })
                with open("posts.json", "w") as file:json.dump(posts, file, indent=4)
                return redirect(url_for("post", post_id=post_id))
            return render_template("post.html", post=p)
    return "Post not found", 404
@app.route("/search")
def search():
    query = request.args.get("q", "").lower()
    with open("posts.json", "r") as file:
        posts = json.load(file)
    results = []
    for post in posts:
        if (query in post["title"].lower()or query in post["username"].lower()or query in post["content"].lower()or any(query in topic.lower() for topic in post.get("topics", []))):results.append(post)
    random.shuffle(results)
    return render_template("home.html", posts=results)
@app.route("/rules", methods=["GET", "POST"])
def rules(): return render_template("rules.html")
@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    raw_password = request.form["password"]
    email = request.form.get("email", "")
    try:
        with open("users.json", "r") as file:users = json.load(file)
    except:users = []
    for user in users:
        if user["username"].lower() == username.lower():return "Username already exists."
    if len(username) < 3:return "Username too short."
    if len(raw_password) < 5:return "Password too short."
    if len(raw_password) > 100:return "Password too long."
    password = generate_password_hash(raw_password)
    reserved = [
    "anonymous",
    "admin",
    "administrator",
    "moderator",
    "system",
    "debatto"
]

    if username.lower() in reserved:return "That username is reserved."
    account = {
        "username": username,
        "password": password,
        "email": email,
        "joined": datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S")
    }
    users.append(account)
    with open("users.json", "w") as file:json.dump(users, file, indent=4)
    session["username"] = username
    return redirect(url_for("index"))
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    try:
        with open("users.json", "r") as file:users = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):users = []
    for user in users:
        if user["username"].lower() == username.lower():
            if check_password_hash(user["password"], password):
                session["username"] = user["username"]
                return redirect(url_for("index"))
            return "Incorrect password."
    return "User not found."
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))
@app.route("/user/<username>")
def profile(username):
    try:
        with open("users.json", "r") as file:users = json.load(file)
    except:return "No users."
    try:
        with open("posts.json", "r") as file:posts = json.load(file)
    except:posts = []
    for user in users:
        if user["username"].lower() == username.lower():
            user_posts = []
            for post in posts:
                if post["username"].lower() == username.lower():user_posts.append(post)
            return render_template(
                "account.html",
                user=user,
                posts=user_posts
            )
    return "User not found.", 404
if __name__ == "__main__":app.run(debug=True)