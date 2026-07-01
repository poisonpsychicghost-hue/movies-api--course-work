from flask import Flask, send_file, jsonify

app = Flask(__name__)

print("App file Loaded")

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/about")
def about():
    print("The /about route was requested")
    return "<h1>This API will manage movie data.</h1>"

@app.route("/movie")
def get_movie():
    print('Movie Route Selected!')
    base_title = "Dazed and Confused"
    year = 1993
    full_title = f"{base_title} ({year})"
    director = "Richard Linklater"

    movie = {
        "id": 1,
        "title": full_title,
        "year": year,
        "director": director
    }
    return jsonify(movie)

if __name__ == '__main__':
    app.run(port=5000, debug=True)