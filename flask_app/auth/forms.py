from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Email, Length, EqualTo

from . import models


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=128)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('e-mail', validators=[DataRequired(), Email(), Length(max=128)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=128)])
    password2 = PasswordField(
        'Repeat Password',
        validators=[DataRequired(), Length(max=128), EqualTo('password')]
    )
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = models.User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = models.User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Please use a different email address.')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('e-mail', validators=[DataRequired(), Email(), Length(max=128)])
    submit = SubmitField('Request password reset')


class PasswordResetForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=128)])
    password2 = PasswordField(
        'Repeat Password',
        validators=[DataRequired(), Length(max=128), EqualTo('password')]
    )
    submit = SubmitField('Reset password')
