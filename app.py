from flask import Flask, send_file, jsonify, request, g, make_response
from philosophers_api import register_philosophers_routes 
from flasgger import Swagger
import sqlite3

app = Flask(__name__)
Swagger(app)

DATABASE = "movies.db"

print("App file Loaded")

def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def error_response(error, message, status):
    return jsonify({"error": error, "message": message}), status

register_philosophers_routes(app, error_response)


movies = [
    {
        "id": 0,
        "title": "Dazed and Confused",
        "director": "Richard Linklater",
        "year": 1993,
        "watched": False,
        "actors": ["Matthew McConaughey"]
    },
    {
        "id": 1,
        "title": "Spirited Away",
        "director": "Hayao Miyazaki",
        "year": 2001,
        "watched": True,
        "actors": ["Rumi Hiiragi"]
    }
]
print("Movies at Startup", movies)

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/about")
def about():
    print("The /about route was requested")
    return "<h1>This API will manage movie data.</h1>"

@app.route("/movies")
def get_movies():
    """
    List all movies
    ---
    responses:
        200:
            description: Returns a list of movies

    """
    print('Movies Route Selected!')
    db = get_db()
    rows = db.execute("SELECT * FROM movies ORDER BY id"
                    ).fetchall()
    movies = [dict(row) for row in rows]
    return jsonify(movies)

@app.route("/movies/<int:id>")
def get_movie(id):
    """
    Locates and Displays a Movie by ID
    ---
    response:
        200:
            description: Locates an indvidual Movie by ID
    """
    db = get_db()
    row = db.execute(
                "SELECT * FROM movies WHERE id = ?",
                (id,),
            ).fetchone()
    
    
    if row is None:
        return error_response("Not Found", f"Movie {id} Not Found", 404)
    return jsonify(dict(row))

@app.route("/directors")
def get_directors():
    """
        List all Directors
        ---
        responses:
            200:
                description: Returns a list of directors
    
        """
    print('Directors Route Selected!')
    db = get_db()
    rows = db.execute("SELECT * FROM directors ORDER BY id"
                        ).fetchall()
    directors = [dict(row) for row in rows]
    return jsonify(directors)

@app.route("/directors/<int:id>")
def get_director(id):
    """
        Locates and Displays a Director by ID
        ---
        response:
            200:
                description: Locates an indvidual Director by ID
        """
    db = get_db()
    row = db.execute(
                "SELECT * FROM directors WHERE id = ?",
                (id,),
            ).fetchone()
        
        
    if row is None:
        return error_response("Not Found", f"Director {id} Not Found", 404)
    return jsonify(dict(row))

@app.route("/directors/<int:id>/full")
def get_director_full(id):
    db = get_db()
    director_row = db.execute(
        "SELECT id, name FROM directors WHERE id = ?",
    (id,),
    ).fetchone()

    if director_row is None:
        return error_response("Not Found", f"Director ID: {id} Not Found", 404)

    movie_rows = db.execute(
        """
            SELECT id, title, year FROM movies WHERE director_id = ? ORDER BY year
        """,
        (id,),).fetchall()

    if not movie_rows:
        return error_response("Not Found", f"Director {id} Has No Movies in Database.", 200)

    movies = [{
        "id": row["id"],
        "title": row["title"],
        "year": row["year"],
    } for row in movie_rows]
    
    return jsonify({
        "director": {
            "id": director_row["id"],
            "name": director_row["name"]
        },
        "movies": movies
    }), 200


@app.get("/movies/<int:id>/full")
def get_movie_full(id):
    db = get_db()
    row = db.execute(
        """
        SELECT
            movies.id,
            movies.title,
            movies.year,
            movies.director_id,
            directors.name AS director_name
        FROM movies
        JOIN directors ON movies.director_id = directors.id
        WHERE movies.id = ?
        """,
        (id,),
    ).fetchone()

    if row is None:
        return error_response("Not Found", f"Movie {id} Not Found.", 404)

    return jsonify(dict(row))

@app.post("/movies")
def create_movie():
    """
    Create a new movie
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            year:
              type: integer
            director: 
                type: string
            watched:
                type: boolean
            actors:
                type: array
                items:
                    type: string
          required:
            - title
            - year
            - director
            - watched
            - actors
    responses:
      201:
        description: Movie created successfully
      400:
        description: Invalid input data
    """
    print('POST /movies hit!')

    if not request.is_json:
        return error_response("Bad Request", "Not valid JSON", 400)

    data = request.get_json()
    print("incoming:", data)

    required_fields = ["title", "director", "year", "watched", "actors"]

    for field in required_fields:
        if field not in data:
            return error_response(
                "Bad Request",
                f"Missing required field: {field}", 400)
    for field in ["title", "director"]:
        value = data.get(field)
        if not isinstance(value, str) or value.strip() == "":
            return error_response("Bad Request",
                f"Field '{field}' must be a non-empty string",
             400)
                
    if not isinstance(data.get("year"), int):
        return error_response(
            "Bad Request",
            "Field 'year' must be an integer",
            400)

    if not isinstance(data.get("watched"), bool):
        return error_response(
            "Bad Request",
            "Field 'watched' must be a boolean", 400)
    actors = data.get("actors")

    if not isinstance(actors, list):
        return error_response(
            "Bad Request",
            "Field 'actors' must be a list of strings",
            400
        )

    if not all(isinstance(item, str) for item in actors):
        return error_response(
            "Bad Request",
            "Each actor in 'actors' must be a string",
            400
        )
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM directors WHERE name = ?", (data["director"],)
        )
        row = cursor.fetchone()
        if row is None:
            return error_response(
                "Bad Request",
                "Unknown director name; create the director first or use a valid director.",
                400
            )
        director_id = row["id"]

        cursor.execute(
            """
                INSERT INTO movies (title, year, director_id)
                VALUES (?, ?, ?)
            """, 
            (data["title"], data["year"], director_id)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        return error_response(
            "Duplication Error",
             "Movie with this title and year already exists.", 409)
    except sqlite3.OperationalError as e:
        msg = e.args[0] if e.args else ""
        if "syntax error" in msg.lower():
            return error_response("Invalid Request", "SQL-Related Issue", 400)
        else: return error_response("Internal Error", "Unexpected database error", 500)



    new_id = cursor.lastrowid

    movie = {
        "id": new_id,
        "title": data["title"],
        "year": data["year"],
        "director": data["director"],
        "watched": data["watched"],
        "actors": data["actors"]
    }

    response = make_response(jsonify(movie), 201)
    response.headers["Location"] = f"/movies/{new_id}"
    return response

@app.post("/directors")
def create_director():
    """
    Creates a new director
    ---
    consumes:
    - application/json
    parameters:
    - in: body
        name: body
        required: true
        schema:
            type: object
            properties:
                name:
                    type: string
            required: 
                - name
    responses:
        201:
            description: Director created successfully
        400:
            description: Invalid input data
    
    """
    if not request.is_json:
        return error_response("Bad Request", "Not Valid JSON", 400)

    data = request.get_json()

    if "name" not in data:
        return error_response(
            "Bad Request",
            "Missing Required Field: name",
            400
        )

    name = data.get("name")
    if not isinstance(name, str) or name.strip() == "":
        return(
            "Bad Request",
            "Field 'name' must be a non-empty string",
            400
        )

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM directors WHERE name = ?",
        (name,)
    )
    existing = cursor.fetchone()
    if existing is not None:
        return error_response(
            "Bad Request",
            "Director with this name already exists",
            400
        )

    cursor.execute(
        "Insert Into directors (name) VALUES (?)",
        (name,)
    )

    conn.commit()

    new_id = cursor.lastrowid

    director = {
        "id": new_id,
        "name": name,
    }

    response = make_response(jsonify(director), 201)
    response.headers["Locations"] = f"/directors/{new_id}"
    return response
    
@app.put("/movies/<int:id>")
def update_movie(id):
    print(f"PUT /movies/{id} hit!")

    # 1) find the existing movie
    movie = next((m for m in movies if m["id"] == id), None)
    if movie is None:
        return error_response(
            "Not Found",
            f"Movie with id {id} not found.",
            404
        )

    # 2) same JSON + validation rules as POST
    if not request.is_json:
        return error_response("Bad Request", "Not valid JSON", 400)

    data = request.get_json()
    print("incoming:", data)

    required_fields = ["title", "director", "year", "watched", "actors"]

    for field in required_fields:
        if field not in data:
            return error_response(
                "Bad Request",
                f"Missing required field: {field}",
                400
            )

    for field in ["title", "director"]:
        value = data.get(field)
        if not isinstance(value, str) or value.strip() == "":
            return error_response(
                "Bad Request",
                f"Field '{field}' must be a non-empty string",
                400
            )

    if not isinstance(data.get("year"), int):
        return error_response(
            "Bad Request",
            "Field 'year' must be an integer",
            400
        )

    if not isinstance(data.get("watched"), bool):
        return error_response(
            "Bad Request",
            "Field 'watched' must be a boolean",
            400
        )
    actors = data.get("actors")

    if not isinstance(actors, list):
        return error_response(
            "Bad Request",
            "Field 'actors' must be a list of strings",
            400
        )

    if not all(isinstance(item, str) for item in actors):
        return error_response(
            "Bad Request",
            "Each actor in 'actors' must be a string",
            400
        )


    # 3) mutate the existing movie (keep id)
    movie["title"] = data["title"]
    movie["director"] = data["director"]
    movie["year"] = data["year"]
    movie["watched"] = data["watched"]
    movie["actors"] = data["actors"]

    print("movies now:", movies)

    # 4) return the updated resource with 200
    return jsonify(movie), 200

@app.delete("/movies/<int:id>")
def delete_movie(id):
    print(f"DELETE /movies/{id} hit!")
    try:
        db = get_db()
        cursor = db.execute(
            "DELETE FROM movies WHERE id = ?",
            (id,),
        )
        db.commit()
    except sqlite3.OperationalError as e:
        msg = e.args[0] if e.args else ""
        if "syntax error" in msg.lower():
            return error_response(
                "Bad Request",
                "SQL-related syntax error in Request.",
                400
            )
        else:
            return error_response(
                "Internal Error",
                "Unexpected database error",
                500
            )
    finally: 
        db.close()

    if cursor.rowcount == 0:
        return error_response(
            "Not Found",
            f"Movie ID {id} Not Found.",
            404
        )
    else:
        return "", 204
    
@app.patch("/movies/<int:id>")
def update_movie_field(id):
    if not request.is_json:
        return error_response("Bad Request", "Not valid JSON", 400)

    data = request.get_json()

    allowed_fields = ["title", "year", "director_id"] #left in for future refactor

    fields = []
    params = []

    if "title" in data:
        fields.append("title = ?")
        params.append(data["title"])

    if "year" in data:
        fields.append("year = ?")
        params.append(data["year"])

    if "director_id" in data:
        fields.append("director_id = ?")
        params.append(data["director_id"])

    if not fields:
        return error_response(
            "Bad Request",
            "No Update Fields Provided",
            400
        )
    db = get_db()

    sql = "UPDATE movies SET " + ", ".join(fields) + " WHERE id = ?"
    params.append(id)

    cursor = db.execute(sql, params)
    db.commit()

    if cursor.rowcount == 0:
        return error_response(
            "Not Found",
            f"Movie with ID {id} Not Found",
            404
        )
    row = db.execute(
        "SELECT * FROM movies WHERE id = ?",
        (id,)
    ).fetchone()
    return jsonify(dict(row)), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True,)