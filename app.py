from flask import Flask, render_template, session
from flask_wtf.csrf import CSRFProtect
import config
from models.cart import Cart
from routes.auth import auth_bp
from routes.products import products_bp
from routes.stock import stock_bp
from routes.cart import cart_bp
from routes.orders import orders_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

csrf = CSRFProtect(app)
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(orders_bp)


@app.context_processor
def inject_cart_count():
    """Makes `cart_count` available in every template."""
    return {"cart_count": Cart(session).count()}


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)