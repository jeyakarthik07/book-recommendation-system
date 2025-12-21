import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset safely
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "final_books_dataset_enhanced.csv")

df = pd.read_csv(DATA_PATH)

# Combine important text features
df["combined_features"] = (
    df["description"].fillna("") + " " +
    df["genre"].fillna("") + " " +
    df["mood"].fillna("") + " " +
    df["book_type"].fillna("")
)

# Convert text to numerical vectors
vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = vectorizer.fit_transform(df["combined_features"])

def recommend_similar_books(book_title, top_n=5):
    matches = df[df["title"].str.contains(book_title, case=False, na=False, regex=False)]

    if matches.empty:
        return "Book not found in dataset"

    idx = matches.index[0]


    similarity_scores = cosine_similarity(
        tfidf_matrix[idx], tfidf_matrix
    ).flatten()

    similar_indices = similarity_scores.argsort()[::-1][1:top_n+1]

    return df.iloc[similar_indices][
        ["title", "authors", "genre", "mood", "popularity_level"]
    ]
