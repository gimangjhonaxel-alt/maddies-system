from flask import (
    Blueprint, render_template, redirect, url_for, flash, session,
    abort, request,
)
from models.inventory import Inventory
from models.order import Order, STATUSES, PAYMENT_STATUSES
from models.user import User
from routes.decorators import role_required

order_manage_bp = Blueprint("order_manage", __name__)


def _manager_branch_id():
    user = User.find_by_id(session["user_id"])
    return user.branch_id if user else None


def _can_manage(order):
    """The owner manages every order. A manager only their own branch's."""
    if session.get("role") == "owner":
        return True
    return order["branch_id"] == _manager_branch_id()


@order_manage_bp.route("/manage/orders")
@role_required("owner", "manager")
def index():
    if session.get("role") == "manager":
        branch_id = _manager_branch_id()
        if not branch_id:
            flash("Your account isn't assigned to a branch yet. "
                  "Please ask the owner.", "warning")
            return redirect(url_for("index"))
        branches = []
    else:
        branches = Inventory.all_branches()
        branch_id = request.args.get("branch", type=int)  # None = all branches

    status = request.args.get("status")
    orders = Order.for_branch(branch_id)
    if status in STATUSES:
        orders = [o for o in orders if o["status"] == status]

    return render_template(
        "order_manage/index.html",
        orders=orders,
        branches=branches,
        selected_branch=branch_id,
        selected_status=status,
        statuses=STATUSES,
    )


@order_manage_bp.route("/manage/orders/<int:order_id>")
@role_required("owner", "manager")
def detail(order_id):
    order = Order.find_by_id(order_id)
    if order is None or not _can_manage(order):
        abort(404)
    return render_template(
        "order_manage/detail.html",
        order=order,
        statuses=STATUSES,
        payment_statuses=PAYMENT_STATUSES,
    )


@order_manage_bp.route("/manage/orders/<int:order_id>/status", methods=["POST"])
@role_required("owner", "manager")
def update_status(order_id):
    order = Order.find_by_id(order_id)
    if order is None or not _can_manage(order):
        abort(404)

    status = request.form.get("status", "")
    payment_status = request.form.get("payment_status", "")
    try:
        Order.update_status(order_id, status, payment_status)
    except ValueError as error:
        flash(str(error), "danger")
    else:
        if status == "cancelled" and order["status"] != "cancelled":
            flash("Order cancelled. Its items were returned to stock.", "info")
        else:
            flash("Order updated.", "success")
    return redirect(url_for("order_manage.detail", order_id=order_id))