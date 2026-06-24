from flask import Flask

app = Flask(__name__)

print("App file Loaded")

if __name__ == '__main__':
    app.run(port=5000, debug=True)