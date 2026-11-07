from flask import (
    Blueprint, render_template, redirect, url_for, flash, session,
    request, abort,
)
from models.cart import Cart
from models.product import Product

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/cart")
def view():
    cart = Cart(session)
    return render_template("cart/index.html", lines=cart.items(), total=cart.total())


@cart_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def add(product_id):
    product = Product.find_by_id(product_id)
    if product is None or not product.is_active:
        abort(404)
    quantity = request.form.get("quantity", 1, type=int)
    if quantity is None or quantity < 1:
        quantity = 1
    Cart(session).add(product_id, quantity)
    flash(f"{product.name} was added to your cart.", "success")
    return redirect(url_for("products.menu"))


@cart_bp.route("/cart/update/<int:product_id>", methods=["POST"])
def update(product_id):
    quantity = request.form.get("quantity", type=int)
    if quantity is None:
        flash("Please enter a valid quantity.", "danger")
    else:
        Cart(session).set_quantity(product_id, quantity)
    return redirect(url_for("cart.view"))


@cart_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove(product_id):
    Cart(session).remove(product_id)
    flash("Item removed from your cart.", "info")
    return redirect(url_for("cart.view"))