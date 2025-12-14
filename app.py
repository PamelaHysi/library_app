from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from ai_agent import answer_query

app = Flask(__name__)
app.secret_key = "supersecret"   

# ---------- DATABASE HELPER ----------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- HOME ----------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        db = get_db()
        db.execute("INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
                   (name, email, password, "user"))
        db.commit()
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, redirect to dashboard
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- USER DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    books = db.execute("SELECT * FROM books WHERE user_id=?", (session["user_id"],)).fetchall()

    return render_template("dashboard.html", books=books)

# ---------- ADD BOOK ----------
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        genre = request.form["genre"]
        status = request.form["status"]

        db = get_db()
        db.execute("INSERT INTO books (title, author, genre, status, user_id) VALUES (?,?,?,?,?)",
                   (title, author, genre, status, session["user_id"]))
        db.commit()
        return redirect(url_for("dashboard"))

    return render_template("add_book.html")

# ---------- EDIT BOOK ----------
@app.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        genre = request.form["genre"]
        status = request.form["status"]

        db.execute("UPDATE books SET title=?, author=?, genre=?, status=? WHERE id=?",
                   (title, author, genre, status, book_id))
        db.commit()
        return redirect(url_for("dashboard"))

    return render_template("edit_book.html", book=book)

# ---------- DELETE BOOK ----------
@app.route("/delete_book/<int:book_id>")
def delete_book(book_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    db = get_db()
    db.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit()
    db.close()
    return redirect(url_for("dashboard"))

# ---------- AI QUERY ----------
@app.route("/ai_query", methods=["GET", "POST"])
def ai_query():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    answer = None
    if request.method == "POST":
        query = request.form.get("query", "")
        answer = answer_query(
            query,
            session.get("user_id"),
            session.get("role")
            )
    
    return render_template("ai_query.html", answer=answer)

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin")
def admin():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    books = db.execute("SELECT * FROM books").fetchall()
    db.close()
    
    return render_template("admin_dashboard.html", users=users, books=books)

# ---------- ADMIN EDIT BOOK ----------
@app.route("/admin_edit_book/<int:book_id>", methods=["GET", "POST"])
def admin_edit_book(book_id):
    if session.get("role") != "admin":
        return "Access denied"

    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()

    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        genre = request.form["genre"]
        status = request.form["status"]

        db.execute("""
            UPDATE books
            SET title=?, author=?, genre=?, status=?
            WHERE id=?
        """, (title, author, genre, status, book_id))
        db.commit()

        return redirect(url_for("admin_dashboard"))

    return render_template("admin_edit_book.html", book=book)


# ---------- ADMIN DELETE BOOK ----------
@app.route("/admin_delete_book/<int:book_id>")
def admin_delete_book(book_id):
    if session.get("role") != "admin":
        return "Access denied"

    db = get_db()
    db.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit()

    return redirect(url_for("admin_dashboard"))

# ---------- ADMIN USER LIST ----------
@app.route("/adminusers")
def admin_users():
    if session.get("role") != "admin":
        return "Access denied"

    db = get_db()
    users = db.execute("""
        SELECT users.*, 
        (SELECT COUNT(*) FROM books WHERE books.user_id = users.id) AS book_count
        FROM users
    """).fetchall()

    return render_template("admin_users.html", users=users)


# ---------- ADMIN EDIT USER ----------
@app.route("/admin_edit_user/<int:user_id>", methods=["GET", "POST"])
def admin_edit_user(user_id):
    if session.get("role") != "admin":
        return "Access denied"

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        role = request.form["role"]

        db.execute("""
            UPDATE users SET name=?, email=?, role=? WHERE id=?
        """, (name, email, role, user_id))
        db.commit()

        return redirect(url_for("admin_users"))

    return render_template("admin_edit_user.html", user=user)


# ---------- ADMIN DELETE USER ----------
@app.route("/admin_delete_user/<int:user_id>")
def admin_delete_user(user_id):
    if session.get("role") != "admin":
        return "Access denied"

    db = get_db()

    # delete all user's books first to avoid foreign key issues
    db.execute("DELETE FROM books WHERE user_id=?", (user_id,))
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()

    return redirect(url_for("admin_users"))


# ---------- ADMIN RESET PASSWORD ----------
@app.route("/admin_reset_password/<int:user_id>", methods=["POST"])
def admin_reset_password(user_id):
    if session.get("role") != "admin":
        return "Access denied"

    new_password = generate_password_hash("1234")  # default reset value

    db = get_db()
    db.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
    db.commit()

    return redirect(url_for("admin_users"))


if __name__ == "__main__":
    app.run(debug=False)