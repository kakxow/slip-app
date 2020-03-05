from flask_sqlalchemy import SQLAlchemy
import connexion
from loguru import logger

from config import Config
from db import Base, Slip
from flask_app.auth import db, models


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
    from .base.views import views as base_views
    from .admin.views import admin_bp
    app.register_blueprint(base_views)
    app.register_blueprint(admin_bp)

    # Register shell context.
    register_shellcontext(app)

    # Run background task.
    from .admin.utils import run_delete_task
    if not app.config['TESTING']:
        run_delete_task()

    return app


def register_shellcontext(app):
    def shell_context():
        return {
            'db': db,
            'User': models.User,
            'Slip': Slip,
            'db_slip': db_slip,
        }
    app.shell_context_processor(shell_context)
