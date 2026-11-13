from flask import (
    Blueprint, render_template, redirect, url_for, flash, session,
)
from forms import RegisterForm, LoginForm, VerifyForm
from mailer import Mailer
from models.user import User

auth_bp = Blueprint("auth", __name__)


def _pending_user():
    """The person who is in the middle of verifying their email, if any."""
    user_id = session.get("pending_verify_id")
    if not user_id:
        return None
    user = User.find_by_id(user_id)
    if user is None or user.email_verified:
        session.pop("pending_verify_id", None)
        return None
    return user


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        email = form.email.data.strip().lower()

        # An old, never-verified sign-up with this email can be redone.
        User.remove_unverified(email)
        user = User.register_customer(name, email, form.password.data)

        code = user.start_verification()
        session["pending_verify_id"] = user.id
        if Mailer.send_verification_code(user.name, user.email, code):
            flash(f"We sent a 6-digit code to {user.email}. "
                  "Enter it below to finish signing up.", "info")
        else:
            flash("We couldn't send the email right now. "
                  "Please use \"resend the code\" below.", "warning")
        return redirect(url_for("auth.verify"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():
    user = _pending_user()
    if user is None:
        flash("Please log in to continue.", "warning")
        return redirect(url_for("auth.login"))

    form = VerifyForm()
    if form.validate_on_submit():
        result = user.check_verification(form.code.data)
        if result == "ok":
            session.pop("pending_verify_id", None)
            flash("Your email is verified! You can now log in.", "success")
            return redirect(url_for("auth.login"))
        if result == "wrong":
            flash("That code isn't right. Please try again.", "danger")
        elif result == "locked":
            flash("Too many wrong tries. Please request a new code.", "danger")
        else:
            flash("That code has expired. Please request a new one.", "warning")

    return render_template(
        "auth/verify.html",
        form=form,
        email=user.email,
        wait=user.seconds_until_resend(),
    )


@auth_bp.route("/verify/resend", methods=["POST"])
def resend_code():
    user = _pending_user()
    if user is None:
        return redirect(url_for("auth.login"))

    wait = user.seconds_until_resend()
    if wait > 0:
        flash(f"Please wait {wait} seconds before asking for a new code.", "warning")
    else:
        code = user.start_verification()
        if Mailer.send_verification_code(user.name, user.email, code):
            flash("We sent you a new code.", "info")
        else:
            flash("We couldn't send the email right now. Please try again.", "warning")
    return redirect(url_for("auth.verify"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data.strip().lower())
        if user and user.check_password(form.password.data):
            if not user.email_verified:
                session["pending_verify_id"] = user.id
                flash("Please verify your email first. Enter the code we "
                      "sent you, or request a new one.", "warning")
                return redirect(url_for("auth.verify"))

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