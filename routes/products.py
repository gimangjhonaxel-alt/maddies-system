import os
import uuid
from flask import (
    Blueprint, render_template, redirect, url_for, flash, abort,
    current_app,
)
from forms import ProductForm
from models.product import Product
from routes.decorators import role_required

products_bp = Blueprint("products", __name__)

UPLOAD_SUBFOLDER = os.path.join("uploads", "products")


def _load_categories(form):
    form.category_id.choices = [
        (c["id"], c["name"]) for c in Product.all_categories()
    ]


def _save_image(file_storage):
    """Save an uploaded image under a random name.
    Returns the path relative to /static, or None if no file was chosen.
    The file type was already checked by the form (jpg, png, webp only)."""
    if not file_storage or not file_storage.filename:
        return None
    extension = file_storage.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"
    folder = os.path.join(current_app.static_folder, UPLOAD_SUBFOLDER)
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))
    return f"uploads/products/{filename}"


@products_bp.route("/menu")
def menu():
    grouped = {}
    for product in Product.get_all():
        grouped.setdefault(product.category_name, []).append(product)
    return render_template("products/menu.html", grouped=grouped)


@products_bp.route("/products")
@role_required("owner", "manager")
def manage():
    products = Product.get_all(include_inactive=True)
    return render_template("products/manage.html", products=products)


@products_bp.route("/products/new", methods=["GET", "POST"])
@role_required("owner", "manager")
def create():
    form = ProductForm()
    _load_categories(form)
    if form.validate_on_submit():
        Product.create(
            form.category_id.data,
            form.name.data.strip(),
            (form.description.data or "").strip(),
            form.price.data,
            _save_image(form.image_file.data),
        )
        flash("Product added to all branches.", "success")
        return redirect(url_for("products.manage"))
    return render_template("products/form.html", form=form, title="Add product")


@products_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@role_required("owner", "manager")
def edit(product_id):
    product = Product.find_by_id(product_id)
    if product is None:
        abort(404)
    form = ProductForm(obj=product)
    _load_categories(form)
    if form.validate_on_submit():
        product.update(
            form.category_id.data,
            form.name.data.strip(),
            (form.description.data or "").strip(),
            form.price.data,
            _save_image(form.image_file.data),
        )
        flash("Product updated.", "success")
        return redirect(url_for("products.manage"))
    return render_template(
        "products/form.html", form=form, title="Edit product", product=product,
    )


@products_bp.route("/products/<int:product_id>/archive", methods=["POST"])
@role_required("owner")
def archive(product_id):
    product = Product.find_by_id(product_id)
    if product is None:
        abort(404)
    product.archive()
    flash(f"{product.name} was removed from the menu.", "info")
    return redirect(url_for("products.manage"))


@products_bp.route("/products/<int:product_id>/restore", methods=["POST"])
@role_required("owner")
def restore(product_id):
    product = Product.find_by_id(product_id)
    if product is None:
        abort(404)
    product.restore()
    flash(f"{product.name} is back on the menu.", "success")
    return redirect(url_for("products.manage"))