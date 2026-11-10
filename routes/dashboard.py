from flask import (
    Blueprint, render_template, session, redirect, url_for, flash,
)
from models.dashboard import Dashboard
from models.inventory import Inventory
from models.order import Order
from models.user import User
from routes.decorators import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    user = User.find_by_id(session["user_id"])
    if user is None:
        session.clear()
        flash("Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    if user.role == "owner":
        return render_template(
            "dashboard/owner.html",
            totals=Dashboard.totals(),
            branches=Dashboard.sales_by_branch(),
            top_products=Dashboard.top_products(),
            low_stock=Dashboard.low_stock(),
        )

    if user.role == "manager":
        if not user.branch_id:
            flash("Your account isn't assigned to a branch yet. "
                  "Please ask the owner.", "warning")
            return redirect(url_for("index"))
        return render_template(
            "dashboard/manager.html",
            branch=Inventory.get_branch(user.branch_id),
            totals=Dashboard.totals(user.branch_id),
            top_products=Dashboard.top_products(user.branch_id),
            low_stock=Dashboard.low_stock(user.branch_id),
            recent_orders=Order.for_branch(user.branch_id)[:5],
        )

    return render_template(
        "dashboard/customer.html",
        orders=Order.for_user(user.id),
    )