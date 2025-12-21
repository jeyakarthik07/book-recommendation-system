import pandas as pd

# Load raw dataset
df = pd.read_csv("data/final_books_dataset_enhanced.csv")

# -------------------------------
# Clean ISBN (CRITICAL)
# -------------------------------
df["isbn"] = (
    df["isbn"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.strip()
)

df.loc[df["isbn"].isin(["nan", "None", ""]), "isbn"] = None

# -------------------------------
# Normalize book titles
# -------------------------------
df["title_clean"] = (
    df["title"]
    .astype(str)
    .str.strip()
)

df["title_lower"] = df["title_clean"].str.lower()

# -------------------------------
# Normalize authors
# -------------------------------
df["author_clean"] = (
    df["authors"]
    .astype(str)
    .str.lower()
    .str.replace(".", "", regex=False)
    .str.replace(" ", "", regex=False)
)

# -------------------------------
# Save CLEAN dataset
# -------------------------------
df.to_csv("data/books_cleaned.csv", index=False)

print("✅ Dataset cleaned and saved as data/books_cleaned.csv")
