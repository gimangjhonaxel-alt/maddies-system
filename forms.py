from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import (
    StringField, PasswordField, SubmitField,
    TextAreaField, DecimalField, SelectField, IntegerField,
)
from wtforms.validators import (
    DataRequired, InputRequired, Email, Length, EqualTo, ValidationError,
    NumberRange, Optional, Regexp,
)
from models.user import User


def _strip(value):
    """Trim stray spaces, which often come from copy-pasting."""
    return value.strip() if isinstance(value, str) else value


class RegisterForm(FlaskForm):
    name = StringField(
        "Full name",
        filters=[_strip],
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    email = StringField(
        "Email",
        filters=[_strip],
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=64)],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(),
                    EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")

    def validate_email(self, field):
        if User.find_by_email(field.data.strip().lower()) and User.find_by_email(field.data.strip().lower()).email_verified:
            raise ValidationError("That email is already registered.")


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        filters=[_strip],
        validators=[DataRequired(), Email()],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class ProfileForm(FlaskForm):
    name = StringField(
        "Full name",
        filters=[_strip],
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    email = StringField(
        "Email",
        filters=[_strip],
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    photo = FileField(
        "Profile photo (optional)",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "webp"],
                        "Only JPG, PNG, or WEBP images are allowed."),
            FileSize(max_size=2 * 1024 * 1024,
                     message="The image must be 2 MB or smaller."),
        ],
    )
    submit = SubmitField("Save profile")

    def __init__(self, user_id=None, **kwargs):
        super().__init__(**kwargs)
        self._user_id = user_id

    def validate_email(self, field):
        if User.email_taken(field.data.strip().lower(), self._user_id):
            raise ValidationError("That email is already used by another account.")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current password", validators=[DataRequired()]
    )
    new_password = PasswordField(
        "New password",
        validators=[DataRequired(), Length(min=8, max=64)],
    )
    confirm_new_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(),
                    EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Change password")


class ProductForm(FlaskForm):
    name = StringField(
        "Product name",
        filters=[_strip],
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(max=500)],
    )
    price = DecimalField(
        "Price (PHP)",
        places=2,
        validators=[DataRequired(),
                    NumberRange(min=1, max=99999,
                                message="Price must be between 1 and 99,999.")],
    )
    image_file = FileField(
        "Product photo (optional)",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "webp"],
                        "Only JPG, PNG, or WEBP images are allowed."),
            FileSize(max_size=2 * 1024 * 1024,
                     message="The image must be 2 MB or smaller."),
        ],
    )
    submit = SubmitField("Save product")


class StockForm(FlaskForm):
    quantity = IntegerField(
        "Quantity",
        validators=[InputRequired(), NumberRange(min=0, max=100000)],
    )
    low_stock_threshold = IntegerField(
        "Low-stock alert at",
        validators=[InputRequired(), NumberRange(min=0, max=10000)],
    )


class CheckoutForm(FlaskForm):
    branch_id = SelectField("Branch", coerce=int, validators=[DataRequired()])
    customer_name = StringField(
        "Full name",
        filters=[_strip],
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    customer_phone = StringField(
        "Mobile number",
        filters=[_strip],
        validators=[
            DataRequired(),
            Regexp(r"^(09\d{9}|\+639\d{9})$",
                   message="Enter a valid mobile number, like 09171234567."),
        ],
    )
    customer_email = StringField(
        "Email (for your order confirmation)",
        filters=[_strip],
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    fulfillment = SelectField(
        "Pickup or delivery",
        choices=[("pickup", "Pickup at the branch"),
                 ("delivery", "Delivery")],
    )
    delivery_address = TextAreaField(
        "Delivery address",
        validators=[Length(max=255)],
    )
    payment_method = SelectField(
        "Payment method",
        choices=[("cash", "Cash (pay on pickup or delivery)"),
                 ("gcash", "GCash")],
    )
    gcash_reference = StringField(
        "GCash reference number",
        filters=[_strip],
        validators=[Length(max=50)],
    )
    submit = SubmitField("Place order")

    def validate_delivery_address(self, field):
        if self.fulfillment.data == "delivery" and not (field.data or "").strip():
            raise ValidationError("Please enter your delivery address.")

    def validate_gcash_reference(self, field):
        if self.payment_method.data == "gcash":
            value = (field.data or "").strip()
            if len(value) < 6:
                raise ValidationError(
                    "Please enter your GCash reference number (at least 6 characters)."
                )
                


class VerifyForm(FlaskForm):
    code = StringField(
        "6-digit code",
        filters=[_strip],
        validators=[
            DataRequired(),
            Regexp(r"^\d{6}$", message="Enter the 6-digit code from your email."),
        ],
    )
    submit = SubmitField("Verify email")