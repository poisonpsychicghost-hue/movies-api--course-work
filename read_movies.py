import sqlite3

def main():
    # with-statement ensures the connection is closed automatically
    with sqlite3.connect("movies.db") as conn:
        cursor = conn.execute("""
            SELECT id, title, year, director_id
            FROM movies;
        """)
        for row in cursor:
            print(row)

if __name__ == "__main__":
    main()