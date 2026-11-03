# Debatto
Where minds clash free

## Run locally

1. Install Python.
2. Install dependencies: `pip install -r requirements.txt`.
3. Create a `.env` file with at least `SECRET_KEY=your-long-random-secret`.
4. Initialize the database: `python init_db.py`.
5. Start the development server: `python newapp.py`.

## Deploy to Railway

Debatto is a Flask application whose entry point is `newapp.py`.

1. Create a Railway project and deploy this GitHub repository.
2. Add a Railway Volume to the web service and set its mount path to `/data`.
3. In the service Variables, set:
   - `SECRET_KEY`: a long, random secret value (keep it private).
   - `DATABASE_PATH`: `/data/debatto.db`
   - `UPLOAD_FOLDER`: `/data/uploads`
4. Set the service Start Command to:

   `python init_db.py && gunicorn --bind 0.0.0.0:$PORT newapp:app`

5. In Settings → Networking, generate a public domain.

The volume is important: without it, SQLite data and uploaded images can be lost when the container is replaced. The same volume stores both the database and uploaded images.

### Important notes

- Do not commit `.env`, the SQLite database, or uploaded user files to Git.
- If you are moving an existing live database from another host, back it up and copy it into the Railway volume before switching traffic. Initializing the schema does not migrate existing user data.
- The database schema initializer uses `CREATE TABLE IF NOT EXISTS`; it creates missing tables but does not alter existing table definitions.
