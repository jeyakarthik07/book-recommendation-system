from backend.ml_recommender import recommend_similar_books

result = recommend_similar_books(
    book_title="Harry Potter and the Half-Blood Prince (Harry Potter  #6)",
    top_n=5
)

print(result)
