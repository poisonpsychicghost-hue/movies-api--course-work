from flask import Flask, send_file, jsonify, request

app = Flask(__name__)

print("App file Loaded")

movies = [
    {
        "id": 0,
        "title": "Dazed and Confused",
        "director": "Richard Linklater",
        "year": 1993,
        "watched": True
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

if __name__ == '__main__':
    app.run(port=5000, debug=True)