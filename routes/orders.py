from flask import (
    Blueprint, render_template, redirect, url_for, flash, session, abort,
)
from forms import CheckoutForm
from models.cart import Cart
from models.inventory import Inventory
from models.order import Order, OutOfStockError
from models.user import User

orders_bp = Blueprint("orders", __name__)


def _remember_order(order_id):
    """Guests can't log in, so remember their recent orders in the session."""
    placed = session.get("placed_orders", [])
    placed.append(order_id)
    session["placed_orders"] = placed[-20:]


def _can_view(order):
    role = session.get("role")
    if role == "owner":
        return True
    if role == "manager":
        user = User.find_by_id(session["user_id"])
        return user is not None and user.branch_id == order["branch_id"]
    user_id = session.get("user_id")
    if user_id and order["user_id"] == user_id:
        return True
    return order["id"] in session.get("placed_orders", [])


@orders_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = Cart(session)
    lines = cart.items()
    if not lines:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("products.menu"))

    form = CheckoutForm()
    form.branch_id.choices = [
        (b["id"], b["name"]) for b in Inventory.all_branches()
    ]

    # Pre-fill the name and email for logged-in customers.
    if not form.is_submitted() and session.get("user_id"):
        user = User.find_by_id(session["user_id"])
        if user:
            form.customer_name.data = user.name
            form.customer_email.data = user.email

    if form.validate_on_submit():
        is_delivery = form.fulfillment.data == "delivery"
        is_gcash = form.payment_method.data == "gcash"
        try:
            order_id = Order.place(
                lines,
                form.branch_id.data,
                session.get("user_id"),
                form.customer_name.data.strip(),
                form.customer_phone.data.strip(),
                form.customer_email.data.strip().lower(),
                form.fulfillment.data,
                form.delivery_address.data.strip() if is_delivery else None,
                form.payment_method.data,
                form.gcash_reference.data.strip() if is_gcash else None,
            )
        except OutOfStockError as error:
            flash(str(error), "danger")
        else:
            cart.clear()
            _remember_order(order_id)
            flash("Your order has been placed!", "success")
            return redirect(url_for("orders.confirmation", order_id=order_id))

    return render_template(
        "orders/checkout.html", form=form, lines=lines, total=cart.total(),
    )


@orders_bp.route("/orders/<int:order_id>/confirmation")
def confirmation(order_id):
    order = Order.find_by_id(order_id)
    if order is None or not _can_view(order):
        abort(404)
    return render_template("orders/confirmation.html", order=order)