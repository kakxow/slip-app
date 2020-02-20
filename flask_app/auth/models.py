from time import time
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from . import db, login
from . import auth


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column('username', db.String(64), unique=True, index=True)
    email = db.Column('email', db.String(128), unique=True, index=True)
    password_hash = db.Column('password', db.String(128))
    verified = db.Column('verified', db.Boolean(), default=False)
    date_created = db.Column('date created', db.DateTime(), default=datetime.now())
    last_query = db.Column('last query', db.String(512))

    def __repr__(self: 'User') -> str:
        return f'User {self.username}'

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in: int = 600) -> str:
        token = jwt.encode(
            {
                'reset_password': self.id,
                'exp': time() + expires_in
            },
            auth.config['SECRET_KEY'],
            algorithm='HS256'
        ).decode('utf-8')
        return token

    @staticmethod
    def verify_reset_password_token(token: str) -> 'User':
        try:
            id = jwt.decode(
                token,
                auth.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except jwt.exceptions.InvalidTokenError:
            return
        return User.query.get(id)

    def get_mail_verification_token(self) -> str:
        token = jwt.encode(
            {'verify_email': self.id},
            auth.config['SECRET_KEY'],
            algorithm='HS256'
        ).decode('utf-8')
        return token

    @staticmethod
    def verify_mail_verification_token(token: str) -> 'User':
        try:
            id = jwt.decode(
                token,
                auth.config['SECRET_KEY'],
                algorithms=['HS256']
            )['verify_email']
        except jwt.exceptions.InvalidTokenError:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id: str) -> User:
    return User.query.get(int(id))
