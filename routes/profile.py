import os
import uuid
from flask import (
    Blueprint, render_template, redirect, url_for, flash, session,
    current_app,
)
from forms import ProfileForm, ChangePasswordForm
from models.user import User
from routes.decorators import login_required

profile_bp = Blueprint("profile", __name__)

PHOTO_FOLDER = os.path.join("uploads", "profiles")


def _current_user():
    user = User.find_by_id(session["user_id"])
    if user is None:
        session.clear()
    return user


def _save_photo(file_storage):
    """Save an uploaded photo under a random name.
    Returns the path relative to /static, or None if no file was chosen.
    The file type was already checked by the form (jpg, png, webp only)."""
    if not file_storage or not file_storage.filename:
        return None
    extension = file_storage.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"
    folder = os.path.join(current_app.static_folder, PHOTO_FOLDER)
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))
    return f"uploads/profiles/{filename}"


def _delete_old_photo(path):
    """Remove an old profile photo, but only inside the profiles folder."""
    if path and path.startswith("uploads/profiles/"):
        full_path = os.path.join(current_app.static_folder, path)
        if os.path.isfile(full_path):
            os.remove(full_path)


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def index():
    user = _current_user()
    if user is None:
        return redirect(url_for("auth.login"))

    form = ProfileForm(user_id=user.id, obj=user)
    if form.validate_on_submit():
        user.update_details(form.name.data.strip(),
                            form.email.data.strip().lower())
        session["name"] = user.name

        new_photo = _save_photo(form.photo.data)
        if new_photo:
            _delete_old_photo(user.profile_photo)
            user.set_photo(new_photo)

        flash("Your profile was updated.", "success")
        return redirect(url_for("profile.index"))

    return render_template(
        "profile/index.html",
        user=user,
        form=form,
        password_form=ChangePasswordForm(),
    )


@profile_bp.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    user = _current_user()
    if user is None:
        return redirect(url_for("auth.login"))

    password_form = ChangePasswordForm()
    if password_form.validate_on_submit():
        if not user.check_password(password_form.current_password.data):
            flash("Your current password is incorrect.", "danger")
        else:
            user.change_password(password_form.new_password.data)
            flash("Your password was changed.", "success")
        return redirect(url_for("profile.index"))

    return render_template(
        "profile/index.html",
        user=user,
        form=ProfileForm(user_id=user.id, obj=user),
        password_form=password_form,
    )