import pandas as pd
import os

# Resolve base directory safely
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "books_cleaned.csv")

# Load dataset ONCE
df = pd.read_csv(DATA_PATH)
df["title_lower"] = df["title"].astype(str).str.strip().str.lower()



def recommend_books(mood, genre=None, age_group=None, top_n=5):
    filtered = df.copy()

    # Mood is primary filter
    if mood:
        filtered = filtered[
            filtered["mood"].str.lower() == mood.lower()
        ]

    # Genre is secondary (contains)
    if genre:
        filtered = filtered[
            filtered["genre"].str.lower().str.contains(genre.lower(), na=False)
        ]

    # Relax age group if no results
    if age_group:
        temp = filtered[
            filtered["target_age_group"].str.lower() == age_group.lower()
        ]
        if not temp.empty:
            filtered = temp

    # Sort by popularity
    filtered = filtered.sort_values(
        by=["popularity_level", "ratings_count"],
        ascending=[False, False],
        na_position="last"
    )

    return filtered.head(top_n)[
        ["title", "authors", "genre", "mood", "target_age_group", "popularity_level"]
    ]
