from cs50 import SQL

db = SQL("sqlite:///finance.db")

checker = db.execute("Select * FROM users WHERE username = ?", "mohamed")

if len(checker) == 1:
    print(checker)
