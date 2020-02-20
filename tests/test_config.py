import os.path as pth
import os

ENV = 'development'
DEBUG = True
TESTING = True
SECRET_KEY = 'test_key'
JSON_AS_ASCII = 0

SQLALCHEMY_TRACK_MODIFICATIONS = False
example_db_path = pth.join(pth.dirname(pth.dirname(__file__)), 'db', 'example_db.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{example_db_path}'

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'test@gmail.com'
MAIL_PASSWORD = '123456789456'
MAIL_FLAG = 1

WTF_CSRF_ENABLED = False
