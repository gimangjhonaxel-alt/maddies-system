from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
import config
from routes.auth import auth_bp
from routes.products import products_bp
from routes.stock import stock_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

csrf = CSRFProtect(app)
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(stock_bp)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)