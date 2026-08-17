from flask import Flask, send_file, jsonify, request, g, make_response
from philosophers_api import register_philosophers_routes
from flasgger import Swagger
import sqlite3
import json

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

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/about")
def about():
    print("The /about route was requested")
    return "<h1>This API will manage movie data.</h1>"


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

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
    rows = db.execute("SELECT * FROM movies ORDER BY id").fetchall()

    movies = []
    for row in rows:
        movie = dict(row)
        movie["actors"] = json.loads(movie["actors"]) if movie["actors"] else []
        movie["genres"] = json.loads(movie["genres"]) if movie["genres"] else []
        movie["watched"] = bool(movie["watched"]) if movie["watched"] is not None else None
        movies.append(movie)

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

    movie = dict(row)
    movie["actors"] = json.loads(movie["actors"]) if movie["actors"] else []
    movie["genres"] = json.loads(movie["genres"]) if movie["genres"] else []
    movie["watched"] = bool(movie["watched"]) if movie["watched"] is not None else None

    return jsonify(movie)

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
    """
    Locates and displays a movie by ID with full detail, including director name.
    ---
    responses:
        200:
            description: Returns the full movie record
        404:
            description: Movie not found
    """
    db = get_db()
    row = db.execute(
        """
        SELECT
            movies.id,
            movies.title,
            movies.year,
            movies.director_id,
            directors.name AS director_name,
            movies.mpaa_rating,
            movies.duration_minutes,
            movies.watched,
            movies.actors,
            movies.genres
        FROM movies
        JOIN directors ON movies.director_id = directors.id
        WHERE movies.id = ?
        """,
        (id,),
    ).fetchone()

    if row is None:
        return error_response("Not Found", f"Movie {id} Not Found.", 404)

    movie = dict(row)
    movie["actors"] = json.loads(movie["actors"]) if movie["actors"] else []
    movie["genres"] = json.loads(movie["genres"]) if movie["genres"] else []
    movie["watched"] = bool(movie["watched"]) if movie["watched"] is not None else None

    return jsonify(movie)


# ---------------------------------------------------------------------------
# POST routes
# ---------------------------------------------------------------------------

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
            mpaa_rating:
                type: string
            duration_minutes:
                type: integer
            watched:
                type: boolean
            actors:
                type: array
                items:
                    type: string
            genres:
                type: array
                items:
                    type: string
          required:
            - title
            - year
            - director
            - duration_minutes
            - watched
            - actors
            - genres
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

    required_fields = ["title", "director", "year", "duration_minutes", "watched", "actors", "genres"]

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

    if not isinstance(data.get("duration_minutes"), int):
        return error_response(
            "Bad Request",
            "Field 'duration_minutes' must be an integer",
            400)

    mpaa_rating = data.get("mpaa_rating")
    if mpaa_rating is not None and not isinstance(mpaa_rating, str):
        return error_response(
            "Bad Request",
            "Field 'mpaa_rating' must be a string if provided",
            400)

    watched_raw = data.get("watched")
    if isinstance(watched_raw, bool):
        watched = 1 if watched_raw else 0
    elif watched_raw in (0, 1):
        watched = watched_raw
    else:
        return error_response(
            "Bad Request",
            "Field 'watched' must be a boolean or 0/1", 400)

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

    genres = data.get("genres")
    if not isinstance(genres, list):
        return error_response(
            "Bad Request",
            "Field 'genres' must be a list of strings",
            400
        )
    if not all(isinstance(item, str) for item in genres):
        return error_response(
            "Bad Request",
            "Each genre in 'genres' must be a string",
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
                INSERT INTO movies
                    (title, year, director_id, mpaa_rating, duration_minutes, watched, actors, genres)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["title"],
                data["year"],
                director_id,
                mpaa_rating,
                data["duration_minutes"],
                watched,
                json.dumps(actors),
                json.dumps(genres),
            )
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
        "mpaa_rating": mpaa_rating,
        "duration_minutes": data["duration_minutes"],
        "watched": bool(watched),
        "actors": actors,
        "genres": genres,
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
        return error_response(
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
    response.headers["Location"] = f"/directors/{new_id}"
    return response


# ---------------------------------------------------------------------------
# PUT route (full replace)
# ---------------------------------------------------------------------------

@app.put("/movies/<int:id>")
def update_movie(id):
    """
    Fully replace an existing movie
    ---
    consumes:
      - application/json
    responses:
      200:
        description: Movie updated successfully
      400:
        description: Invalid input data
      404:
        description: Movie not found
      409:
        description: Duplicate title/year
    """
    print(f"PUT /movies/{id} hit!")

    db = get_db()
    existing = db.execute(
        "SELECT id FROM movies WHERE id = ?", (id,)
    ).fetchone()
    if existing is None:
        return error_response(
            "Not Found",
            f"Movie with id {id} not found.",
            404
        )

    if not request.is_json:
        return error_response("Bad Request", "Not valid JSON", 400)

    data = request.get_json()
    print("incoming:", data)

    required_fields = ["title", "director", "year", "duration_minutes", "watched", "actors", "genres"]

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

    if not isinstance(data.get("duration_minutes"), int):
        return error_response(
            "Bad Request",
            "Field 'duration_minutes' must be an integer",
            400
        )

    mpaa_rating = data.get("mpaa_rating")
    if mpaa_rating is not None and not isinstance(mpaa_rating, str):
        return error_response(
            "Bad Request",
            "Field 'mpaa_rating' must be a string if provided",
            400
        )

    watched_raw = data.get("watched")
    if isinstance(watched_raw, bool):
        watched = 1 if watched_raw else 0
    elif watched_raw in (0, 1):
        watched = watched_raw
    else:
        return error_response(
            "Bad Request",
            "Field 'watched' must be a boolean or 0/1",
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

    genres = data.get("genres")
    if not isinstance(genres, list):
        return error_response(
            "Bad Request",
            "Field 'genres' must be a list of strings",
            400
        )
    if not all(isinstance(item, str) for item in genres):
        return error_response(
            "Bad Request",
            "Each genre in 'genres' must be a string",
            400
        )

    try:
        cursor = db.cursor()

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
                UPDATE movies
                SET title = ?, year = ?, director_id = ?, mpaa_rating = ?,
                    duration_minutes = ?, watched = ?, actors = ?, genres = ?
                WHERE id = ?
            """,
            (
                data["title"],
                data["year"],
                director_id,
                mpaa_rating,
                data["duration_minutes"],
                watched,
                json.dumps(actors),
                json.dumps(genres),
                id,
            )
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        return error_response(
            "Duplication Error",
            "Movie with this title and year already exists.", 409)
    except sqlite3.OperationalError as e:
        msg = e.args[0] if e.args else ""
        if "syntax error" in msg.lower():
            return error_response("Invalid Request", "SQL-Related Issue", 400)
        else: return error_response("Internal Error", "Unexpected database error", 500)

    movie = {
        "id": id,
        "title": data["title"],
        "year": data["year"],
        "director": data["director"],
        "mpaa_rating": mpaa_rating,
        "duration_minutes": data["duration_minutes"],
        "watched": bool(watched),
        "actors": actors,
        "genres": genres,
    }

    return jsonify(movie), 200


# ---------------------------------------------------------------------------
# DELETE route
# ---------------------------------------------------------------------------

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

    if cursor.rowcount == 0:
        return error_response(
            "Not Found",
            f"Movie ID {id} Not Found.",
            404
        )
    else:
        return "", 204


# ---------------------------------------------------------------------------
# PATCH route (partial update)
# ---------------------------------------------------------------------------

@app.patch("/movies/<int:id>")
def update_movie_field(id):
    """
    Partially update a movie
    ---
    consumes:
      - application/json
    responses:
      200:
        description: Movie updated successfully
      400:
        description: Invalid input data
      404:
        description: Movie not found
      409:
        description: Duplicate title/year
    """
    if not request.is_json:
        return error_response("Bad Request", "Not valid JSON", 400)

    data = request.get_json()

    allowed_fields = [
        "title", "year", "director", "mpaa_rating",
        "duration_minutes", "watched", "actors", "genres",
    ]

    fields = []
    params = []

    if "title" in data:
        value = data.get("title")
        if not isinstance(value, str) or value.strip() == "":
            return error_response(
                "Bad Request",
                "Field 'title' must be a non-empty string",
                400
            )
        fields.append("title = ?")
        params.append(value)

    if "year" in data:
        if not isinstance(data.get("year"), int):
            return error_response(
                "Bad Request",
                "Field 'year' must be an integer",
                400
            )
        fields.append("year = ?")
        params.append(data["year"])

    if "director" in data:
        value = data.get("director")
        if not isinstance(value, str) or value.strip() == "":
            return error_response(
                "Bad Request",
                "Field 'director' must be a non-empty string",
                400
            )
        db = get_db()
        row = db.execute(
            "SELECT id FROM directors WHERE name = ?", (value,)
        ).fetchone()
        if row is None:
            return error_response(
                "Bad Request",
                "Unknown director name; create the director first or use a valid director.",
                400
            )
        fields.append("director_id = ?")
        params.append(row["id"])

    if "mpaa_rating" in data:
        value = data.get("mpaa_rating")
        if value is not None and not isinstance(value, str):
            return error_response(
                "Bad Request",
                "Field 'mpaa_rating' must be a string if provided",
                400
            )
        fields.append("mpaa_rating = ?")
        params.append(value)

    if "duration_minutes" in data:
        if not isinstance(data.get("duration_minutes"), int):
            return error_response(
                "Bad Request",
                "Field 'duration_minutes' must be an integer",
                400
            )
        fields.append("duration_minutes = ?")
        params.append(data["duration_minutes"])

    if "watched" in data:
        watched_raw = data.get("watched")
        if isinstance(watched_raw, bool):
            watched = 1 if watched_raw else 0
        elif watched_raw in (0, 1):
            watched = watched_raw
        else:
            return error_response(
                "Bad Request",
                "Field 'watched' must be a boolean or 0/1",
                400
            )
        fields.append("watched = ?")
        params.append(watched)

    if "actors" in data:
        actors = data.get("actors")
        if not isinstance(actors, list) or not all(isinstance(item, str) for item in actors):
            return error_response(
                "Bad Request",
                "Field 'actors' must be a list of strings",
                400
            )
        fields.append("actors = ?")
        params.append(json.dumps(actors))

    if "genres" in data:
        genres = data.get("genres")
        if not isinstance(genres, list) or not all(isinstance(item, str) for item in genres):
            return error_response(
                "Bad Request",
                "Field 'genres' must be a list of strings",
                400
            )
        fields.append("genres = ?")
        params.append(json.dumps(genres))

    if not fields:
        return error_response(
            "Bad Request",
            "No Update Fields Provided",
            400
        )

    db = get_db()
    sql = "UPDATE movies SET " + ", ".join(fields) + " WHERE id = ?"
    params.append(id)

    try:
        cursor = db.execute(sql, params)
        db.commit()
    except sqlite3.IntegrityError as e:
        return error_response(
            "Duplication Error",
            "Movie with this title and year already exists.", 409)
    except sqlite3.OperationalError as e:
        msg = e.args[0] if e.args else ""
        if "syntax error" in msg.lower():
            return error_response("Invalid Request", "SQL-Related Issue", 400)
        else: return error_response("Internal Error", "Unexpected database error", 500)

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

    movie = dict(row)
    movie["actors"] = json.loads(movie["actors"]) if movie["actors"] else []
    movie["genres"] = json.loads(movie["genres"]) if movie["genres"] else []
    movie["watched"] = bool(movie["watched"]) if movie["watched"] is not None else None

    return jsonify(movie), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True,)