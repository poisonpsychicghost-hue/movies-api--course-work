import sqlite3

def main():
    with sqlite3.connect('movies.db') as conn:
        cursor = conn.cursor()
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT 
                m.id as 'movie_id',
                m.title as 'movie_title',
                m.year as 'release_year',
                d.name as 'director_name'
            FROM movies as m
            INNER JOIN directors as d
                ON m.director_id = d.id
            ORDER BY m.year DESC
        """)

        rows = cursor.fetchall()

        top_movies = [dict(row) for row in rows]
        print(top_movies)

if __name__ == "__main__":
    main()
    