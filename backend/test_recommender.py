from backend.recommender import recommend_books

results = recommend_books(
    mood="Happy",
    genre="fiction",
    age_group="Adult",
    top_n=5
)

print(results)
