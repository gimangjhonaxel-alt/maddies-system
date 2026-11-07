from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import (
    StringField, PasswordField, SubmitField,
    TextAreaField, DecimalField, SelectField, IntegerField,
)
from wtforms.validators import (
    DataRequired, InputRequired, Email, Length, EqualTo, ValidationError,
    NumberRange, Optional,
)
from models.user import User


class RegisterForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    email = StringField(
        "Email",
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
        if User.find_by_email(field.data.strip().lower()):
            raise ValidationError("That email is already registered.")


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class ProductForm(FlaskForm):
    name = StringField(
        "Product name",
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