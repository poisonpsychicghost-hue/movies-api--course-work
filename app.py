from flask import Flask, send_file

app = Flask(__name__)

print("App file Loaded")

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/about")
def about():
    print("The /about route was requested")
    return "<h1>This API will manage movie data.</h1>"



if __name__ == '__main__':
    app.run(port=5000, debug=True)