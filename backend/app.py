import os
from flask import Flask, render_template, request
from backend.recommender import df
from backend.ml_recommender import recommend_similar_books

# --------------------------------------------------
# App setup
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# --------------------------------------------------
# Home page
# --------------------------------------------------
@app.route("/")
def home():
    popular_books = (
        df.sort_values(by="ratings_count", ascending=False)
          .head(5)[["title", "authors"]]
    )

    moods = sorted(df["mood"].dropna().unique())
    genres = sorted(df["genre"].dropna().unique())

    return render_template(
        "index.html",
        popular_books=popular_books,
        moods=moods,
        genres=genres
    )

# --------------------------------------------------
# Recommend / Search
# --------------------------------------------------
@app.route("/recommend", methods=["POST"])
def recommend():
    book_name = (request.form.get("book_name") or "").strip().lower()
    author = (request.form.get("author") or "").strip().lower()
    isbn = (request.form.get("isbn") or "").strip()
    publisher = (request.form.get("publisher") or "").strip()
    mood = (request.form.get("mood") or "").strip()
    genre = (request.form.get("genre") or "").strip()

    data = df.copy()

    # Defensive normalization
    data["title_lower"] = data["title"].astype(str).str.strip().str.lower()
    data["author_clean"] = (
        data["authors"]
        .astype(str)
        .str.lower()
        .str.replace(".", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    # --------------------------------------------------
    # ISBN → DETAIL PAGE ONLY
    # --------------------------------------------------
    if isbn != "":
        matches = data[data["isbn"].astype(str) == isbn]

        return render_template(
            "book_detail.html",
            book=matches.iloc[0] if not matches.empty else None,
            ml_results=None
        )

    # --------------------------------------------------
    # BOOK NAME → EXACT → DETAIL, ELSE PARTIAL → RESULTS
    # --------------------------------------------------
    if book_name != "":
        exact = data[data["title_lower"] == book_name]

        # Exact title → book detail
        if not exact.empty:
            ml_results = recommend_similar_books(exact.iloc[0]["title"], top_n=5)

            return render_template(
                "book_detail.html",
                book=exact.iloc[0],
                ml_results=ml_results
            )

        # Partial title → results + ML
        results = data[data["title_lower"].str.contains(book_name, na=False)]

        ml_results = recommend_similar_books(book_name, top_n=5)

        return render_template(
            "results.html",
            results=results,
            ml_results=ml_results
        )


    # --------------------------------------------------
    # PUBLISHER
    # --------------------------------------------------
    if publisher != "":
        results = data[
            data["publisher"].astype(str).str.contains(publisher, case=False, na=False)
        ]

        return render_template(
            "results.html",
            results=results,
            ml_results = recommend_similar_books(publisher, top_n=5)
        )

    # --------------------------------------------------
    # AUTHOR
    # --------------------------------------------------
    if author != "":
        author_key = author.replace(".", "").replace(" ", "")
        results = data[data["author_clean"].str.contains(author_key, na=False)]

        ml_results = recommend_similar_books(author, top_n=5)

        return render_template(
            "results.html",
            results=results,
            ml_results=ml_results
        )


    # --------------------------------------------------
    # FILTERS (MOOD / GENRE)
    # --------------------------------------------------
    if mood:
        data = data[data["mood"].str.lower() == mood.lower()]

    if genre:
        data = data[data["genre"].str.lower() == genre.lower()]

    ml_results = recommend_similar_books(
        f"{mood} {genre}".strip(), top_n=5
    )

    return render_template(
        "results.html",
        results=data.head(10),
        ml_results=ml_results
    )


# --------------------------------------------------
# BOOK DETAIL PAGE (CLICK FROM RESULTS)
# --------------------------------------------------
@app.route("/book/<path:title>")
def book_detail(title):
    title = title.lower().strip()

    data = df.copy()
    data["title_lower"] = data["title"].astype(str).str.strip().str.lower()

    book = data[data["title_lower"] == title]

    ml_results = None
    if not book.empty:
        ml_results = recommend_similar_books(book.iloc[0]["title"], top_n=5)

    return render_template(
        "book_detail.html",
        book=book.iloc[0] if not book.empty else None,
        ml_results=ml_results
    )

# --------------------------------------------------
# Run app
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
