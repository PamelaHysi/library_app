import sqlite3

def answer_query(text, user_id, role):

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
    elif "popular genre" in text or "most popular" in text:
        result = db.execute("""
        SELECT genre, COUNT(*) AS total
        FROM books
        GROUP BY genre
        ORDER BY total DESC
        LIMIT 1
        """).fetchone()
        return f"The most popular genre is {result['genre']}."
    
    # Total number of books
    elif "how many books" in text or "total books" in text:
        result = db.execute("SELECT COUNT(*) AS total FROM books").fetchone()
        return f"There are {result['total']} books in the library."

    # Books per user
    elif "books per user" in text or "each user" in text:
        results = db.execute("""
        SELECT users.name, COUNT(books.id) AS total
        FROM users
        LEFT JOIN books ON users.id = books.user_id
        GROUP BY users.id
    """).fetchall()
        answer = "Books per user:\n"
        for r in results:
            answer += f"{r['name']}: {r['total']} books\n"
        return answer
    
    # Current reading status
    elif "currently reading" in text or "what am i reading" in text:
        if role == "admin":
            results = db.execute("""
        SELECT title FROM books WHERE status='reading'
    """).fetchall()
        else:
            results = db.execute("""
                SELECT title FROM books
                WHERE status='reading' AND user_id=?
            """, (user_id,)).fetchall()

        if not results:
            return "No books are currently being read."
        else:
            titles = ", ".join([r["title"] for r in results])
            return f"Currently reading: {titles}"

    # Completed books
    elif "completed books" in text or "which books are completed" in text:
        if role == "admin":
            results = db.execute("""
            SELECT title FROM books WHERE status='completed'
        """).fetchall()
        else:
            results = db.execute("""
            SELECT title FROM books
            WHERE status='completed' AND user_id=?
        """, (user_id,)).fetchall()

        if not results:
            answer = "No completed books found."
        else:
            titles = ", ".join([r["title"] for r in results])
            return f"Completed books: {titles}"

    # Default response
    db.close()
    return "Sorry, I don't understand your question."

