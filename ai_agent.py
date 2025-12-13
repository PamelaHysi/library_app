import sqlite3

def answer_query(text):
    text = text.lower()
    db = sqlite3.connect("database.db")
    db.row_factory = sqlite3.Row

    # Who owns the most books?
    if "most books" in text:
        result = db.execute("""
        SELECT users.name, COUNT(books.id) AS total
        FROM users
        JOIN books ON users.id = books.user_id
        GROUP BY users.id
        ORDER BY total DESC
        LIMIT 1
        """).fetchone()
        if result:
            return f"{result['name']} owns the most books ({result['total']})."

    # Most popular genre
    if "popular genre" in text or "most popular" in text:
        result = db.execute("""
        SELECT genre, COUNT(*) AS total
        FROM books
        GROUP BY genre
        ORDER BY total DESC
        LIMIT 1
        """).fetchone()
        return f"The most popular genre is {result['genre']}."

    return "Sorry, I don't understand your question."
