import os
import os.path as pth

example_db_path = pth.join(pth.dirname(__file__), 'db', 'example_db.db')


class Config:
    # Flask settings.
    ENV = os.getenv('FLASK_ENV', 'production')
    TESTING = os.getenv('TESTING', 0)
    SECRET_KEY = os.getenv('SECRET_KEY', 'not_very_secret')
    # Flask-SQLAlchemy settings.
    SQLALCHEMY_DATABASE_URI = \
        os.getenv('DATABASE_URL', f'sqlite:///{example_db_path}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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
    JSON_AS_ASCII = False
    API_PASSWORD = os.getenv(
        'DB_PASSWORD',
        '5693dc6ae18590585a2961c160a2f508a5b4692aa155bd39ae296803ff942ae26bd9c65edefd02511d3f419731c1fb97d7775774636594764c88f6f9ea15f18e'
    )
    API_USER = os.getenv('API_USER', 'user')


POPPLER_PATH = os.getenv(
    'POPPLER_PATH',
    pth.join(pth.dirname(__file__), 'poppler', 'bin', 'pdftotext.exe')
)
# Root directory for slip_crawler.
slip_dir = os.getenv('SLIP_DIR', r'\\Msk-vm-slip\SLIP')
slip_db = Config.SQLALCHEMY_DATABASE_URI

PAGE_SIZE = int(os.getenv('PAGE_SIZE', 20))
