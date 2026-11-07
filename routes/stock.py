from flask import (
    Blueprint, render_template, redirect, url_for, flash, session, abort,
)
from forms import StockForm
from models.inventory import Inventory
from models.user import User
from routes.decorators import role_required

stock_bp = Blueprint("stock", __name__)


def _can_open_branch(branch_id):
    """The owner can open any branch. A manager can only open their own."""
    if session.get("role") == "owner":
        return True
    user = User.find_by_id(session["user_id"])
    return user is not None and user.branch_id == branch_id


@stock_bp.route("/stock")
@role_required("owner", "manager")
def index():
    if session.get("role") == "manager":
        user = User.find_by_id(session["user_id"])
        if user is None or not user.branch_id:
            flash("Your account isn't assigned to a branch yet. "
                  "Please ask the owner.", "warning")
            return redirect(url_for("index"))
        return redirect(url_for("stock.branch_stock", branch_id=user.branch_id))

    branches = Inventory.all_branches()
    if not branches:
        flash("There are no branches yet.", "warning")
        return redirect(url_for("index"))
    return redirect(url_for("stock.branch_stock", branch_id=branches[0]["id"]))


@stock_bp.route("/stock/<int:branch_id>")
@role_required("owner", "manager")
def branch_stock(branch_id):
    if not _can_open_branch(branch_id):
        abort(403)
    branch = Inventory.get_branch(branch_id)
    if branch is None:
        abort(404)
    is_owner = session.get("role") == "owner"
    return render_template(
        "stock/index.html",
        branch=branch,
        branches=Inventory.all_branches() if is_owner else [],
        items=Inventory.for_branch(branch_id),
    )


@stock_bp.route("/stock/<int:branch_id>/<int:product_id>", methods=["POST"])
@role_required("owner", "manager")
def update(branch_id, product_id):
    if not _can_open_branch(branch_id):
        abort(403)
    form = StockForm()
    if form.validate_on_submit():
        Inventory.update(
            branch_id, product_id,
            form.quantity.data, form.low_stock_threshold.data,
        )
        flash("Stock updated.", "success")
    else:
        flash("Please enter whole numbers of 0 or more.", "danger")
    return redirect(url_for("stock.branch_stock", branch_id=branch_id))