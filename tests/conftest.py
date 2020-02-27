import pytest

from flask_app import db_slip, create_app
from flask_app.auth import db, models
from .slip_obj import SlipFactory


@pytest.fixture(scope='session')
def test_client():
    flask_app = create_app()
    testing_client = flask_app.test_client()
    ctx = flask_app.app_context()
    ctx.push()
    yield testing_client
    ctx.pop()


@pytest.fixture(scope='session', autouse=True)
def init_database(test_client):
    db_slip.create_all()
    db.create_all()

    db_slip.session.add_all([SlipFactory.build() for _ in range(10000)])
    user = models.User(
        username='test_user',
        email='test_user@test.test',
        verified=True
    )
    user.set_password('test')
    db.session.add(user)
    db.session.commit()
    yield db, db_slip
    db_slip.drop_all()
    db.drop_all()
