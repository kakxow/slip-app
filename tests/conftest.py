import os

import pytest

test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.py')
os.environ['FLASK_APPLICATION_SETTINGS'] = test_config_path
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
print('environ set')

from flask_app import db_slip, create_app
from flask_app.auth import db, models
from .slip_obj import SlipFactory


@pytest.fixture(scope='session')
def test_client():
    flask_app = create_app()
    print(flask_app.config['SQLALCHEMY_DATABASE_URI'])
    testing_client = flask_app.test_client()
    ctx = flask_app.app_context()
    ctx.push()
    yield testing_client
    ctx.pop()


@pytest.fixture(scope='session')
def init_database(test_client):
    db_slip.create_all()
    db_slip.session.add_all([SlipFactory.build() for _ in range(10000)])
    yield db_slip
    db_slip.drop_all()


@pytest.fixture(scope='module', autouse=True)
def init_database_auth(test_client):
    db.create_all()
    user = models.User(
        username='test_user',
        email='test_user@test.test',
        is_verified=True,
        is_active=True,
    )
    user.set_password('test')
    db.session.add(user)
    db.session.commit()
    yield db
    db.drop_all()


"""
@pytest.fixture(scope='session', autouse=True)
def init_database(test_client):
    db_slip.create_all()
    db.create_all()

    db_slip.session.add_all([SlipFactory.build() for _ in range(10000)])
    user = models.User(
        username='test_user',
        email='test_user@test.test',
        verified=True,
        admin_approved=True,
        is_active=True,
    )
    user.set_password('test')
    db.session.add(user)
    db.session.commit()
    yield db, db_slip
    db_slip.drop_all()
    db.drop_all()
"""
