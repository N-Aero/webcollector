from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return ">2020.01.032-YDP6732<"

@app.route("/No")
def no():
    return ">2020.Banana<"


if __name__ == "__main__":
    app.run(debug=True)