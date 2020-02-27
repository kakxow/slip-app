from flask_wtf import FlaskForm
from wtforms import (DateField, IntegerField, StringField, BooleanField,
                     PasswordField)
from wtforms.validators import DataRequired, Email, Length, Optional


class UserForm(FlaskForm):
    id = IntegerField('User ID', validators=[DataRequired()])
    date_created = DateField('Date created', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Password', validators=[Optional(), Length(min=4, max=128)])
    email = StringField('E-mail', validators=[DataRequired(), Email(), Length(max=128)])
    verified = BooleanField('Verified')
    admin_approved = BooleanField('Approved')
    admin_rights = BooleanField('Admin')
    last_query = StringField(Length(max=512))


class NewUserForm(UserForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, max=128)])
