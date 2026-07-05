from flask import Flask, send_file, jsonify, request

app = Flask(__name__)

print("App file Loaded")

movies = [
    {
        "id": 0,
        "title": "Dazed and Confused",
        "director": "Richard Linklater",
        "year": 1993,
        "watched": False
    },
    {
        "id": 1,
        "title": "Spirited Away",
        "director": "Hayao Miyazaki",
        "year": 2001,
        "watched": True
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
    print('Movies Route Selected!')

    director = request.args.get("director")
    
    if director is None: 
        return jsonify(movies)
    
    filtered = [m for m in movies if m["director"] == director]
    return jsonify(filtered)

@app.route("/movies/<int:id>")
def get_movie(id):
    movie = next((m for m in movies if m["id"] == id), None)

    if movie is None:
        return jsonify({
            "error": {
                "message": "Movie not found",
                "resource": "movie",
                "id": id
            }
        }), 404

    return jsonify(movie)

@app.post("/movies")
def create_movie():
    print('POST /movies hit!')

    if not request.is_json:
        return jsonify({"error": "Not valid JSON"}), 400

    data = request.get_json()
    print("incoming:", data)

    # 1) compute a new id based on current movies
    if movies:
        new_id = max(m["id"] for m in movies) + 1
    else:
        new_id = 0

    # 2) build the movie dict the server will store
    movie = {
        "id": new_id,
        "title": data["title"],
        "director": data["director"],
        "year": data["year"],
        "watched": data["watched"],
    }

    # 3) mutate the in-memory list
    movies.append(movie)
    print("movies now:", movies)

    # 4) return the created resource with 201
    return jsonify(movie), 201



if __name__ == '__main__':
    app.run(port=5000, debug=True)