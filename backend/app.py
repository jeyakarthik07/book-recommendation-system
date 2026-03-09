import os
import re
from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import init_db, get_db_connection
from backend.recommender import df
from backend.ml_recommender import recommend_similar_books

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.secret_key = "dev-secret-key"
init_db()

@app.context_processor
def inject_user():
    return dict(username=session.get("username"))

# --------------------------------------------------
# Home page (Protected)
# --------------------------------------------------
@app.route("/")
def home():

    if "role" not in session:
        return redirect(url_for("login"))

    popular_books = (
        df.sort_values(by="ratings_count", ascending=False)
        .head(5)[["title", "authors", "isbn"]]
    )

    moods = sorted(df["mood"].dropna().str.strip().unique())
    genres = sorted(df["genre"].dropna().str.strip().unique())

    return render_template(
        "index.html",
        popular_books=popular_books,
        moods=moods,
        genres=genres,
        username=session.get("username")
    )

# --------------------------------------------------
# Book detail page (Protected)
# --------------------------------------------------
# --------------------------------------------------
# Book detail page (Protected)
# --------------------------------------------------
@app.route("/book/<isbn>")
def book_detail(isbn):

    if "user_id" not in session:
        return redirect(url_for("login"))

    isbn = str(isbn).strip()

    # -----------------------------
    # 1️⃣ CHECK DATASET
    # -----------------------------
    data = df.copy()
    data["isbn"] = data["isbn"].astype(str).str.strip()

    book = data[data["isbn"] == isbn]

    if not book.empty:

        ml_results = recommend_similar_books(book.iloc[0]["title"], top_n=5)

        return render_template(
            "book_detail.html",
            book=book.iloc[0],
            ml_results=ml_results
        )

    # -----------------------------
    # 2️⃣ CHECK ADMIN BOOKS
    # -----------------------------
    conn = get_db_connection()

    admin_book = conn.execute(
        "SELECT * FROM admin_books"
    ).fetchall()

    conn.close()

    for b in admin_book:

        if str(b["isbn"]).strip() == isbn:

            book_data = {
                "title": b["title"],
                "authors": b["authors"],
                "publisher": b["publisher"],
                "genre": b["genre"],
                "mood": b["mood"],
                "isbn": b["isbn"],
                "num_pages": b["num_pages"],
                "description": b["description"],
                "average_rating": b["average_rating"]
            }

            return render_template(
                "book_detail.html",
                book=book_data,
                ml_results=None
            )

    # -----------------------------
    # 3️⃣ BOOK NOT FOUND
    # -----------------------------
    return render_template(
        "book_detail.html",
        book=None,
        ml_results=None
    )


# --------------------------------------------------
# Recommend / Search (Protected)
# --------------------------------------------------
# --------------------------------------------------
# Recommend / Search (Protected)
# --------------------------------------------------
@app.route("/recommend", methods=["POST"])
def recommend():

    if "user_id" not in session:
        return redirect(url_for("login"))

    book_name = (request.form.get("book_name") or "").strip().lower()
    author = (request.form.get("author") or "").strip().lower()
    isbn = (request.form.get("isbn") or "").strip()
    publisher = (request.form.get("publisher") or "").strip().lower()
    mood = (request.form.get("mood") or "").strip().lower()
    genre = (request.form.get("genre") or "").strip().lower()

    import pandas as pd

    # ---------------------------------
    # LOAD DATASET BOOKS
    # ---------------------------------
    data = df.copy()

    # ---------------------------------
    # LOAD ADMIN BOOKS FROM DATABASE
    # ---------------------------------
    conn = get_db_connection()

    admin_books = conn.execute(
        "SELECT title, authors, publisher, genre, mood, num_pages, average_rating, isbn, description FROM admin_books"
    ).fetchall()

    conn.close()

    import pandas as pd

    if admin_books:

        admin_df = pd.DataFrame(admin_books, columns=[
            "title",
            "authors",
            "publisher",
            "genre",
            "mood",
            "num_pages",
            "average_rating",
            "isbn",
            "description"
        ])


        data = pd.concat([data, admin_df], ignore_index=True)

    # ---------------------------------
    # NORMALIZATION
    # ---------------------------------
    data["title_lower"] = data["title"].astype(str).str.lower().str.strip()

    data["author_clean"] = (
        data["authors"]
        .astype(str)
        .str.lower()
        .str.replace(".", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    data["mood_lower"] = data["mood"].astype(str).str.lower().str.strip()
    data["genre_lower"] = data["genre"].astype(str).str.lower().str.strip()
    data["isbn"] = data["isbn"].astype(str).str.strip()

    # ---------------------------------
    # ISBN SEARCH
    # ---------------------------------
    if isbn:

        book = data[data["isbn"] == isbn]

        return render_template(
            "book_detail.html",
            book=book.iloc[0] if not book.empty else None,
            ml_results=None
        )

    # ---------------------------------
    # BOOK NAME SEARCH
    # ---------------------------------
    if book_name:

        exact = data[data["title_lower"] == book_name]

        if not exact.empty:

            try:
                ml_results = recommend_similar_books(exact.iloc[0]["title"])
            except:
                ml_results = None

            return render_template(
                "book_detail.html",
                book=exact.iloc[0],
                ml_results=ml_results
            )

        results = data[data["title_lower"].str.contains(book_name, na=False)]

        ml_results = recommend_similar_books(book_name)

        return render_template(
            "results.html",
            results=results,
            ml_results=ml_results
        )

    # ---------------------------------
    # AUTHOR SEARCH
    # ---------------------------------
    if author:

        key = author.replace(".", "").replace(" ", "")

        results = data[data["author_clean"].str.contains(key, na=False)]

        ml_results = recommend_similar_books(author)

        return render_template(
            "results.html",
            results=results,
            ml_results=ml_results
        )

    # ---------------------------------
    # PUBLISHER SEARCH
    # ---------------------------------
    if publisher:

        results = data[data["publisher"].astype(str).str.lower().str.contains(publisher, na=False)]

        ml_results = recommend_similar_books(publisher)

        return render_template(
            "results.html",
            results=results,
            ml_results=ml_results
        )

    # ---------------------------------
    # MOOD / GENRE FILTER
    # ---------------------------------
    filtered = data

    if mood and genre:

        filtered = data[
            (data["mood_lower"] == mood) &
            (data["genre_lower"] == genre)
        ]

        if filtered.empty:
            filtered = data[data["mood_lower"] == mood]

        if filtered.empty:
            filtered = data[data["genre_lower"] == genre]

    elif mood:
        filtered = data[data["mood_lower"] == mood]

    elif genre:
        filtered = data[data["genre_lower"] == genre]

    return render_template(
        "results.html",
        results=filtered,
        ml_results=None
    )

# --------------------------------------------------
# Login
# --------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if "role" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        user_id = request.form.get("user_id").strip()
        password = request.form.get("password")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conn.close()

        if user and user["status"] == "blocked":
            flash("Your account has been blocked by admin.")
            return redirect(url_for("login"))

        if user and check_password_hash(user["password_hash"], password):

            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("home"))
        else:
            flash("Invalid Email or Password.")

    return render_template("login.html")

#guest login
@app.route("/guest-login")
def guest_login():

    session["user_id"] = "guest"
    session["username"] = "Guest"
    session["role"] = "guest"

    return redirect(url_for("home"))

# --------------------------------------------------
# Register
# --------------------------------------------------

@app.route("/register", methods=["POST"])
def register():

    user_id = request.form.get("user_id").strip()
    username = request.form.get("username").strip()
    password = request.form.get("password")
    confirm = request.form.get("confirm")

    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    if not re.match(email_pattern, user_id):
        flash("Use proper email id.")
        return redirect(url_for("login"))

    if len(password) < 8:
        flash("Password should have at least 8 characters.")
        return redirect(url_for("login"))

    if password != confirm:
        flash("Password and Confirm Password must be same.")
        return redirect(url_for("login"))

    if not username:
        flash("Username cannot be empty.")
        return redirect(url_for("login"))

    password_hash = generate_password_hash(password)

    try:
        conn = get_db_connection()

        conn.execute(
            "INSERT INTO users (user_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
            (user_id, username, password_hash, "user")
        )

        conn.commit()
        conn.close()

        flash("Account created successfully. Please log in.")

    except Exception:
        flash("User ID or Username already exists.")

    return redirect(url_for("login"))



# --------------------------------------------------
# Logout
# --------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------

@app.route("/admin")
def admin_dashboard():

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    conn = get_db_connection()

    total_users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    recent_users = conn.execute(
        "SELECT username, user_id FROM users ORDER BY id DESC LIMIT 5"
    ).fetchall()

    conn.close()

    total_books = len(df)

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_books=total_books,
        recent_users=recent_users
    )

# --------------------------------------------------
# ADMIN - ANALYTICS
# --------------------------------------------------

@app.route("/admin/analytics")
def admin_analytics():

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    conn = get_db_connection()

    # total users
    total_users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    # admin added books
    total_admin_books = conn.execute(
        "SELECT COUNT(*) FROM admin_books"
    ).fetchone()[0]

    conn.close()

    # dataset books
    total_dataset_books = len(df)

    # most common genre
    top_genre = df["genre"].mode()[0]

    return render_template(
        "admin_analytics.html",
        total_users=total_users,
        total_admin_books=total_admin_books,
        total_dataset_books=total_dataset_books,
        top_genre=top_genre
    )

# --------------------------------------------------
# ADMIN - USER MANAGEMENT
# --------------------------------------------------

@app.route("/admin/users")
def admin_users():

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    conn = get_db_connection()

    users = conn.execute(
        "SELECT id, username, user_id, role, status FROM users ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "admin_users.html",
        users=users
    )

# --------------------------------------------------
# ADMIN - VIEW ADMIN ADDED BOOKS
# --------------------------------------------------

@app.route("/admin/books")
def admin_books():

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    conn = get_db_connection()

    books = conn.execute(
        "SELECT * FROM admin_books ORDER BY created_at DESC LIMIT 50"
    ).fetchall()

    conn.close()

    moods = sorted(df["mood"].dropna().unique())

    return render_template(
        "admin_books.html",
        books=books,
        moods=moods
    )

# --------------------------------------------------
# ADMIN - ADD NEW BOOK
# --------------------------------------------------

@app.route("/admin/add-book", methods=["POST"])
def add_admin_book():

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    title = request.form.get("title")
    authors = request.form.get("authors")
    publisher = request.form.get("publisher")
    agegroup = request.form.get("agegroup")
    language = request.form.get("language")
    popularity = request.form.get("popularity")
    genre = request.form.get("genre")
    mood = request.form.get("mood")
    pages = request.form.get("pages")
    isbn = request.form.get("isbn")
    description = request.form.get("description")

    conn = get_db_connection()

    conn.execute("""
    INSERT INTO admin_books
    (title, authors, publisher, genre, mood, num_pages, average_rating, isbn, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,(title,authors,publisher,genre,mood,pages,popularity,isbn,description))

    conn.commit()

    # ------------------------------
    # KEEP ONLY LATEST 50 BOOKS
    # ------------------------------
    conn.execute("""
    DELETE FROM admin_books
    WHERE id NOT IN (
        SELECT id FROM admin_books
        ORDER BY created_at DESC
        LIMIT 50
    )
    """)

    conn.commit()
    conn.close()

    return redirect(url_for("admin_books"))

# --------------------------------------------------
# ADMIN - DELETE BOOK
# --------------------------------------------------

@app.route("/admin/delete-book/<int:book_id>")
def delete_admin_book(book_id):

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    edit_mode = request.args.get("edit")

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM admin_books WHERE id=?",
        (book_id,)
    )

    conn.commit()
    conn.close()

    if edit_mode:
        return redirect(url_for("admin_books"))

    return redirect(url_for("admin_books"))

# --------------------------------------------------
# ADMIN - EDIT BOOK PAGE
# --------------------------------------------------

@app.route("/admin/edit-book/<int:book_id>")
def edit_admin_book(book_id):

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    conn = get_db_connection()

    book = conn.execute(
        "SELECT * FROM admin_books WHERE id=?",
        (book_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit_book.html",
        book=book
    )

# --------------------------------------------------
# ADMIN - UPDATE BOOK
# --------------------------------------------------

@app.route("/admin/update-book/<int:book_id>", methods=["POST"])
def update_admin_book(book_id):

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    title = request.form.get("title")
    authors = request.form.get("authors")
    publisher = request.form.get("publisher")
    genre = request.form.get("genre")
    mood = request.form.get("mood")
    isbn = request.form.get("isbn")
    pages = request.form.get("num_pages")
    rating = request.form.get("average_rating")
    description = request.form.get("description")

    conn = get_db_connection()

    conn.execute("""
    INSERT INTO admin_books
    (title, authors, publisher, genre, mood, num_pages, average_rating, isbn, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (title, authors, publisher, genre, mood, pages, rating, isbn, description)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_books"))


# --------------------------------------------------
# ADMIN - DELETE USER
# --------------------------------------------------

@app.route("/admin/delete-user/<int:user_id>")
def delete_user(user_id):

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    conn = get_db_connection()

    # prevent admin from deleting themselves
    current_admin = session.get("user_id")

    user = conn.execute(
        "SELECT user_id FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if user and user["user_id"] != current_admin:
        conn.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        conn.commit()

    conn.close()

    return redirect(url_for("admin_users"))

# --------------------------------------------------
# ADMIN - BLOCK USER
# --------------------------------------------------

@app.route("/admin/block-user/<int:user_id>")
def block_user(user_id):

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    conn = get_db_connection()

    conn.execute(
        "UPDATE users SET status='blocked' WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_users"))


# --------------------------------------------------
# ADMIN - UNBLOCK USER
# --------------------------------------------------

@app.route("/admin/unblock-user/<int:user_id>")
def unblock_user(user_id):

    if "role" not in session or session["role"] != "admin":
        return redirect(url_for("home"))

    conn = get_db_connection()

    conn.execute(
        "UPDATE users SET status='active' WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin_users"))



if __name__ == "__main__":
    app.run(debug=True)
