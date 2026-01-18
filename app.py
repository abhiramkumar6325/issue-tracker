print("APP STARTED")

from flask import Flask, render_template, request, redirect, abort
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

DB_PATH = "issues.db"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# =========================
# DB Helpers
# =========================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Issues table
    c.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sl_no TEXT,
        description TEXT,
        module TEXT,
        sub_module TEXT,
        product TEXT,
        resolution TEXT,
        status TEXT,
        priority TEXT,
        owner_browser_id TEXT,
        tags TEXT
    )
    """)

    # Comments table
    c.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER,
        comment TEXT,
        created_at TEXT
    )
    """)

    # Attachments table
    c.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER,
        filename TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================
# DASHBOARD
# =========================
@app.route("/")
@app.route("/dashboard")
def dashboard():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM issues")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM issues WHERE status='To Do'")
    todo = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM issues WHERE status='In Progress'")
    inprogress = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM issues WHERE status='Done'")
    done = c.fetchone()[0]

    conn.close()
    return render_template("dashboard.html", total=total, todo=todo, inprogress=inprogress, done=done)

# =========================
# ADD ISSUE
# =========================
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":

        conn = get_db()
        c = conn.cursor()

        description = request.form["description"]
        resolution = request.form["resolution"]

        # Duplicate detection
        like = f"%{description[:20]}%"
        c.execute("SELECT id FROM issues WHERE description LIKE ? OR resolution LIKE ?", (like, like))
        dup = c.fetchone()

        if dup:
            conn.close()
            return render_template("add.html", error="⚠ Similar issue already exists. Please search before adding.")

        tags = request.form.get("tags", "")

        data = (
            request.form["sl_no"],
            request.form["description"],
            request.form["module"],
            request.form["sub_module"],
            request.form["product"],
            request.form["resolution"],
            request.form["status"],
            request.form["priority"],
            request.form["owner_browser_id"],
            tags
        )

        c.execute("""
        INSERT INTO issues 
        (sl_no, description, module, sub_module, product, resolution, status, priority, owner_browser_id, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        issue_id = c.lastrowid

        # Save attachment
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(save_path)
                c.execute("INSERT INTO attachments (issue_id, filename) VALUES (?, ?)", (issue_id, filename))

        conn.commit()
        conn.close()

        return redirect("/board")

    return render_template("add.html")

# =========================
# ALL ISSUES
# =========================
@app.route("/issues")
def issues_list():
    status = request.args.get("status")
    priority = request.args.get("priority")
    tag = request.args.get("tag")

    conn = get_db()
    c = conn.cursor()

    query = "SELECT * FROM issues WHERE 1=1"
    params = []

    if status:
        query += " AND status=?"
        params.append(status)

    if priority:
        query += " AND priority=?"
        params.append(priority)

    if tag:
        query += " AND tags=?"
        params.append(tag)

    query += " ORDER BY id DESC"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    return render_template("issues.html", rows=rows, status=status, priority=priority, tag=tag)

# =========================
# MY ISSUES
# =========================
@app.route("/my")
def my_issues():
    bid = request.args.get("bid")
    if not bid:
        return "Browser ID missing", 400

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM issues WHERE owner_browser_id=? ORDER BY id DESC", (bid,))
    rows = c.fetchall()
    conn.close()

    return render_template("my.html", rows=rows, bid=bid)

# =========================
# ISSUE DETAILS
# =========================
@app.route("/issue/<int:issue_id>")
def issue_details(issue_id):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM issues WHERE id=?", (issue_id,))
    issue = c.fetchone()

    c.execute("SELECT * FROM comments WHERE issue_id=? ORDER BY id DESC", (issue_id,))
    comments = c.fetchall()

    c.execute("SELECT * FROM attachments WHERE issue_id=?", (issue_id,))
    attachments = c.fetchall()

    conn.close()

    if not issue:
        abort(404)

    return render_template("issue_details.html", issue=issue, comments=comments, attachments=attachments)

# =========================
# ADD COMMENT
# =========================
@app.route("/add_comment/<int:issue_id>", methods=["POST"])
def add_comment(issue_id):
    comment = request.form["comment"]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO comments (issue_id, comment, created_at) VALUES (?, ?, ?)",
              (issue_id, comment, created_at))
    conn.commit()
    conn.close()

    return redirect(f"/issue/{issue_id}")

# =========================
# UPLOAD ATTACHMENT
# =========================
@app.route("/upload/<int:issue_id>", methods=["POST"])
def upload_file(issue_id):
    if "file" not in request.files:
        return redirect(f"/issue/{issue_id}")

    file = request.files["file"]
    if file.filename == "":
        return redirect(f"/issue/{issue_id}")

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO attachments (issue_id, filename) VALUES (?, ?)", (issue_id, filename))
    conn.commit()
    conn.close()

    return redirect(f"/issue/{issue_id}")

# =========================
# KANBAN BOARD
# =========================
@app.route("/board")
def board():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM issues WHERE status='To Do' ORDER BY id DESC")
    todo = c.fetchall()

    c.execute("SELECT * FROM issues WHERE status='In Progress' ORDER BY id DESC")
    inprogress = c.fetchall()

    c.execute("SELECT * FROM issues WHERE status='Done' ORDER BY id DESC")
    done = c.fetchall()

    conn.close()
    return render_template("board.html", todo=todo, inprogress=inprogress, done=done)

# =========================
# MOVE CARD
# =========================
@app.route("/move/<int:issue_id>/<new_status>")
def move_issue(issue_id, new_status):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE issues SET status=? WHERE id=?", (new_status, issue_id))
    conn.commit()
    conn.close()
    return redirect("/board")

# =========================
# SEARCH (FULL JIRA STYLE)
# =========================
@app.route("/search")
def search():
    q = request.args.get("q", "")

    conn = get_db()
    c = conn.cursor()

    like = f"%{q}%"
    c.execute("""
    SELECT * FROM issues
    WHERE description LIKE ? 
       OR module LIKE ? 
       OR product LIKE ? 
       OR sub_module LIKE ?
       OR resolution LIKE ?
       OR tags LIKE ?
    ORDER BY id DESC
    """, (like, like, like, like, like, like))

    rows = c.fetchall()
    conn.close()

    return render_template("search.html", rows=rows, q=q)

# =========================
# START
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

