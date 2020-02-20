from flask_sqlalchemy import SQLAlchemy
import connexion
from loguru import logger

from config import Config
from db import Base


db_slip = SQLAlchemy(model_class=Base)


def create_app():
    """Initialize the core application."""
    logger.remove()
    logger.add(
        'logs/app_log_{time}.log',
        rotation='1 day',
        retention='15 days',
        level='DEBUG'
    )
    connexion_app = connexion.FlaskApp(__name__)
    schema_path = Config.SCHEMA_PATH
    from . import api
    connexion_app.add_api(schema_path, strict_validation=True, validate_responses=True)

    app = connexion_app.app
    app.config.from_object(Config)
    app.config.from_envvar('FLASK_APPLICATION_SETTINGS', silent=True)

    # Initialize extensions.
    from . import auth
    auth.init_app(app)
    db_slip.init_app(app)

    # Register base blueprint.
    from .base import views
    app.register_blueprint(views.views)

    return app
