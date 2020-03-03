from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    IntegerField,
    StringField,
    BooleanField,
    PasswordField,
    ValidationError
)
from wtforms.validators import DataRequired, Email, Length, Optional


from flask_app.auth.models import User


class UserForm(FlaskForm):
    user_id = IntegerField('User ID', validators=[DataRequired()])
    date_created = DateField('Date created', validators=[Optional()])
    username = StringField('Username', validators=[Optional(), Length(min=4, max=64)])
    password = PasswordField('Password', validators=[Optional(), Length(min=4, max=128)])
    email = StringField('E-mail', validators=[Optional(), Email(), Length(max=128)])
    is_verified = BooleanField('Verified')
    is_active = BooleanField('Active')
    is_admin = BooleanField('Admin')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != self.user_id.data:
            raise ValidationError('Please use different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != self.user_id.data:
            raise ValidationError('Please use different email address.')


class NewUserForm(UserForm):
    # Same as UserForm, but everything is required.
    date_created = DateField('Date created', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('E-mail', validators=[DataRequired(), Email(), Length(max=128)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=128)])
