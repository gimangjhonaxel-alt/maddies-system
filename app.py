from flask import Flask, render_template, session
from flask_wtf.csrf import CSRFProtect, CSRFError
import config
from mailer import mail
from models.cart import Cart
from routes.auth import auth_bp
from routes.products import products_bp
from routes.stock import stock_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.order_manage import order_manage_bp
from routes.dashboard import dashboard_bp
from routes.profile import profile_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # uploads: 4 MB at most
app.config.update(
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_USE_TLS=config.MAIL_USE_TLS,
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER=config.MAIL_DEFAULT_SENDER,
)

mail.init_app(app)
csrf = CSRFProtect(app)
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(order_manage_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(profile_bp)


@app.context_processor
def inject_cart_count():
    """Makes `cart_count` available in every template."""
    return {"cart_count": Cart(session).count()}


# ---------- friendly error pages ----------
def show_error(code, title, message):
    return render_template(
        "errors/error.html", code=code, title=title, message=message
    ), code


@app.errorhandler(400)
def bad_request(error):
    return show_error(400, "Something went wrong",
                      "We couldn't process that request. Please go back and try again.")


@app.errorhandler(CSRFError)
def csrf_error(error):
    return show_error(400, "Your session expired",
                      "For your security, the form expired. "
                      "Please go back, refresh the page, and try again.")


@app.errorhandler(403)
def forbidden(error):
    return show_error(403, "You don't have access to this page",
                      "This page is only for Maddie's staff. "
                      "If you think this is a mistake, please log in with the right account.")


@app.errorhandler(404)
def not_found(error):
    return show_error(404, "Page not found",
                      "We couldn't find the page you're looking for. "
                      "It may have been moved or removed.")


@app.errorhandler(405)
def method_not_allowed(error):
    return show_error(405, "That didn't work",
                      "This page can't be opened that way. Please use the buttons on the site.")


@app.errorhandler(413)
def too_large(error):
    return show_error(413, "File too large",
                      "That file is too big. Please choose an image under 2 MB.")


@app.errorhandler(500)
def server_error(error):
    return show_error(500, "Something went wrong on our side",
                      "Sorry about that! Please try again in a moment.")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)