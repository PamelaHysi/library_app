import sqlite3
from werkzeug.security import generate_password_hash

db = sqlite3.connect("database.db")

email = "admin@test.com"
password = "1234"   # you can change this
hashed = generate_password_hash(password)


db.execute("""
INSERT INTO users (name, email, password, role)
VALUES (?, ?, ?, ?)
""", ("Admin", email, hashed, "admin"))

db.commit()
db.close()

print("Admin user created:", email, "password:", password)
