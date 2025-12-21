# 📚 ML-Based Book Recommendation System

An academic project that recommends books using **rule-based filtering** and **machine learning–based similarity**, built with **Python, Flask, Pandas, and Scikit-learn**.

---

## 👤👤 Developed By
**R Jeya Karthik**  
**S Muthu Manikandan** 
Academic Project – 2025

---

## 🎯 Project Objective
To build a web-based system that helps users discover books by searching using:
- Book name
- Author
- ISBN
- Publisher
- Mood
- Genre  

The system ensures that users always receive recommendations using a **hybrid approach**.

---

## 🧠 System Approach

### 🔹 Rule-Based Recommendation
Uses filters such as:
- Author
- Genre
- Mood
- Publisher
- Popularity

### 🔹 ML-Based Recommendation
Uses **content similarity** to recommend books when:
- Rule-based results are empty
- Partial or vague queries are used
- The user wants discovery beyond exact matches

---

## 🧩 Key Features
- 🔍 Search by multiple fields
- 📖 Detailed book view page
- 🤖 ML-based similar book recommendations
- 🔗 Clickable navigation between results and details
- 📊 Popular books section
- 🧼 Cleaned and consistent dataset
- 🗂 Version-controlled using Git & GitHub

---

## 🛠 Tech Stack
- **Frontend**: HTML (CSS ready for extension)
- **Backend**: Flask (Python)
- **ML & Data**: Pandas, Scikit-learn
- **Version Control**: Git & GitHub

---

## 📁 Project Structure
book-recommendation-system/
│
├── backend/
│ ├── app.py
│ ├── recommender.py
│ ├── ml_recommender.py
│ └── preprocess.py
│
├── data/
│ └── books_cleaned.csv
│
├── templates/
│ ├── index.html
│ ├── results.html
│ └── book_detail.html
│
├── requirements.txt
└── README.md


---

## ▶ How to Run the Project

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python -m backend.app

Open browser and visit:

http://127.0.0.1:5000