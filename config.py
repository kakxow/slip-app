import os
import os.path as pth

example_db_path = pth.join(pth.dirname(__file__), 'db', 'example_db.db')


class Config:
    # Flask settings.
    ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('FLASK_DEBUG', 0)
    TESTING = os.getenv('TESTING', 0)
    SECRET_KEY = os.getenv('SECRET_KEY', 'not_very_secret')
    JSON_AS_ASCII = os.getenv('JSON_AS_ASCII', 0)
    # Flask-SQLAlchemy settings.
    SQLALCHEMY_DATABASE_URI = \
        os.getenv('DATABASE_URL', f'sqlite:///{example_db_path}')
    SQLALCHEMY_TRACK_MODIFICATIONS = \
        os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 0)
    # Flask-Mail settings.
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_FLAG = all(
        (MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD)
    )
    # API settings.
    SCHEMA_PATH = \
        pth.join(pth.dirname(__file__), 'flask_app', 'api', 'openapischema.yaml')

    DB_PASSWORD = os.getenv('DB_PASSWORD', 'SecurityFlaw')


POPPLER_PATH = os.getenv(
    'POPPLER_PATH',
    pth.join(pth.dirname(__file__), 'poppler', 'bin', 'pdftotext.exe')
)
# Root directory for slip_crawler.
slip_dir = os.getenv('SLIP_DIR', r'\\Msk-vm-slip\SLIP')
slip_db = Config.SQLALCHEMY_DATABASE_URI

PAGE_SIZE = int(os.getenv('PAGE_SIZE', 20))
