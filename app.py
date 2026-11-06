from flask import Flask, render_template
import config
from models.database import Database

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
db = Database()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dbtest")
def dbtest():
    branches = db.fetch_all("SELECT id, name FROM branches")
    return f"Connected! Branches found: {branches}"


if __name__ == "__main__":
    app.run(debug=True)