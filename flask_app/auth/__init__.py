from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask import Flask, Blueprint

auth = Blueprint('auth', __name__, template_folder='templates')
auth.config = {}

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()


def init_app(app: Flask) -> None:
    """
    Initiates all necessary extensions for auth module.

    Parameters
    ----------
    app
        Flask application to initiate extensions with.

    Returns
    -------
    None

    """
    with app.app_context():
        from . import models, views

        app.register_blueprint(auth)
        db.init_app(app)
        migrate.init_app(app, db)

        login.init_app(app)
        login.login_view = 'auth.login'

        mail.init_app(app)
