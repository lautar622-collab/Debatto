PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    joined TEXT NOT NULL,
    role TEXT DEFAULT 'User'
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    level INTEGER NOT NULL,
    date TEXT NOT NULL,
    userid INTEGER,
    language TEXT NOT NULL DEFAULT 'en',
    FOREIGN KEY (userid) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mediatype TEXT NOT NULL,
    url TEXT NOT NULL,
    name TEXT,
    postid INTEGER,
    FOREIGN KEY (postid) REFERENCES posts (id)
);

CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    type TEXT NOT NULL,
    date TEXT NOT NULL,
    userid INTEGER,
    postid INTEGER,
    responseid INTEGER,
    FOREIGN KEY (userid) REFERENCES users (id),
    FOREIGN KEY (postid) REFERENCES posts (id),
    FOREIGN KEY (responseid) REFERENCES responses (id)
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS postversion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    newdate TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    userid INTEGER,
    postid INTEGER,
    FOREIGN KEY (userid) REFERENCES users (id),
    FOREIGN KEY (postid) REFERENCES posts (id)
);

CREATE TABLE IF NOT EXISTS post_topics (
    postid INTEGER NOT NULL,
    topicid INTEGER NOT NULL,
    PRIMARY KEY (postid, topicid),
    FOREIGN KEY (postid) REFERENCES posts (id),
    FOREIGN KEY (topicid) REFERENCES topics (id)
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    postid INTEGER NOT NULL,
    userid INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    UNIQUE (postid, userid),
    FOREIGN KEY (postid) REFERENCES posts (id),
    FOREIGN KEY (userid) REFERENCES users (id)
);
