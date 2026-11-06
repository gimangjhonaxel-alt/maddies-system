from flask import (
    Blueprint, render_template, redirect, url_for, flash, session,
)
from forms import RegisterForm, LoginForm
from models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        User.register_customer(
            form.name.data.strip(),
            form.email.data.strip().lower(),
            form.password.data,
        )
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data.strip().lower())
        if user and user.check_password(form.password.data):
            session.clear()
            session["user_id"] = user.id
            session["role"] = user.role
            session["name"] = user.name
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("index"))
        flash("Incorrect email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))