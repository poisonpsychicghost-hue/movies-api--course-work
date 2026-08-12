import sqlite3

def main():
    # with-statement ensures the connection is closed automatically
    with sqlite3.connect("movies.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor = conn.execute("""
            SELECT m.title, m.year as 'release_year', d.name as 'directed_by'
            FROM movies as m
            INNER JOIN directors as d
            ON m.director_id = d.id
            ;
        """)

        rows = cursor.fetchall()

        movies = [dict(row) for row in rows]
        print(movies)

if __name__ == "__main__":
    main()