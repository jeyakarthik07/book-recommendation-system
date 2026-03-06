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
    # 🔐 If user not logged in → redirect to login
    if "user_id" not in session:
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
@app.route("/book/<isbn>")
def book_detail(isbn):
    if "user_id" not in session:
        return redirect(url_for("login"))

    data = df.copy()
    data["isbn"] = data["isbn"].astype(str).str.strip()

    book = data[data["isbn"] == isbn]

    if book.empty:
        return render_template(
            "book_detail.html",
            book=None,
            ml_results=None
        )

    ml_results = recommend_similar_books(book.iloc[0]["title"], top_n=5)

    return render_template(
        "book_detail.html",
        book=book.iloc[0],
        ml_results=ml_results
    )


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

    data = df.copy()

    # NORMALIZATION
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

    # ISBN search → detail
    if isbn:
        book = data[data["isbn"] == isbn]
        return render_template(
            "book_detail.html",
            book=book.iloc[0] if not book.empty else None,
            ml_results=None
        )

    # BOOK NAME
    if book_name:
        exact = data[data["title_lower"] == book_name]

        if not exact.empty:
            ml_results = recommend_similar_books(exact.iloc[0]["title"])
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

    # AUTHOR
    if author:
        key = author.replace(".", "").replace(" ", "")
        results = data[data["author_clean"].str.contains(key, na=False)]
        ml_results = recommend_similar_books(author)

        return render_template(
            "results.html",
            results=results,
            ml_results=ml_results
        )

    # PUBLISHER
    if publisher:
        results = data[data["publisher"].astype(str).str.lower().str.contains(publisher, na=False)]
        ml_results = recommend_similar_books(publisher)

        return render_template(
            "results.html",
            results=results,
            ml_results=ml_results
        )

    # SMART FILTER LOGIC
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
    if request.method == "POST":
        user_id = request.form.get("user_id").strip()
        password = request.form.get("password")

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        else:
            flash("Invalid Email or Password.")

    return render_template("login.html")


# --------------------------------------------------
# Register
# --------------------------------------------------

@app.route("/register", methods=["POST"])
def register():
    user_id = request.form.get("user_id").strip()
    username = request.form.get("username").strip()
    password = request.form.get("password")
    confirm = request.form.get("confirm")

    # ---------------- VALIDATION ----------------

    # Email format validation
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_pattern, user_id):
        flash("Use proper email id.")
        return redirect(url_for("login"))

    # Password length
    if len(password) < 8:
        flash("Password should have at least 8 characters.")
        return redirect(url_for("login"))

    # Confirm password
    if password != confirm:
        flash("Password and Confirm Password must be same.")
        return redirect(url_for("login"))

    # Username empty check
    if not username:
        flash("Username cannot be empty.")
        return redirect(url_for("login"))

    password_hash = generate_password_hash(password)

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (user_id, username, password_hash) VALUES (?, ?, ?)",
            (user_id, username, password_hash)
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


if __name__ == "__main__":
    app.run(debug=True)
