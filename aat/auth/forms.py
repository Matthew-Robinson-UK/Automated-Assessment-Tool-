from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    ValidationError,
    Regexp,
    EqualTo,
)

from ..models import User

class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Regexp(
                "^[a-z]{6,8}$",
                message="Your username should be between 6 and 8 characters long, and should only contain lowercase letters",
            ),
            EqualTo(
                "confirm_username",
                message="This does not match the username you entered",
            ),
        ],
    )
    confirm_username = StringField("Confirm Username", validators=[DataRequired()])
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(),
            Regexp(
                r"^(?=.*\d)[A-Za-z\d]{8,25}$",
                message="Password must be between 8 and 25 characters, and contain at least one but not all numeric characters",
            ),
        ],
    )
    register = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(
                "This username has already been taken. Please choose another one."
            )


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


