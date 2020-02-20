import os

import pytest

test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.py')
os.environ['FLASK_APPLICATION_SETTINGS'] = test_config_path

from flask_app import create_app
from flask_app.auth import db, models


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()
    testing_client = flask_app.test_client()
    ctx = flask_app.app_context()
    ctx.push()
    yield testing_client
    ctx.pop()


@pytest.fixture(scope='module')
def init_database():
    user = models.User(
        username='test_user',
        email='test_user@test.test',
        verified=True
    )
    user.set_password('test')
    db.session.add(user)
    db.session.commit()
    yield db
    db.session.delete(user)
    db.session.commit()


@pytest.fixture(scope='function')
def login(test_client):
    form = {'username': 'test_user', 'password': 'test'}
    yield test_client.post('/login', data=form)
    test_client.get('/logout')


def test_index_get(test_client, init_database, login):
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'Reference Retrieval Number' in response.data


def test_index_get_no_login(test_client):
    target_location = 'login'
    response = test_client.get('/')
    assert response.status_code == 302
    assert target_location in response.location


def test_index_post(test_client, init_database, login):
    response = test_client.post('/')
    assert response.status_code == 405


def test_index_with_session_form_data(test_client, init_database, login):
    form_data = {
        'merchant_name': 'Some merchant_name',
        'object_code': 'LP31',
        'pos_id': '87654321',
        'start_date': '2020-01-01',
        'end_date': '2020-01-02',
        'card_number': '1514',
        'start_summ': '888888',
        'end_summ': '999999',
        'ref_num': '123456789123',
        'auth_code': 'T1EST2',
    }
    with test_client.session_transaction() as session:
        session['form_data'] = form_data
    response = test_client.get('/')
    for value in form_data.values():
        assert value in str(response.data)


def test_output_get_no_login(test_client):
    target_location = 'login'
    with test_client:
        response = test_client.get('/output?page=1')
        assert response.status_code == 302
        assert target_location in response.location


def test_output_get(test_client, init_database, login):
    response = test_client.get('/output?page=1')
    assert response.status_code == 200


def test_output_post_no_login(test_client):
    target_location = 'login'
    form_data = {
        'merchant_name': 'Some merchant_name',
        'object_code': 'LP31',
        'pos_id': '87654321',
        'start_date': '2020-01-01',
        'end_date': '2020-01-02',
        'card_number': '1514',
        'start_summ': '888888',
        'end_summ': '999999',
        'ref_num': '123456789123',
        'auth_code': 'T1EST2',
    }
    response = test_client.post('/output?page=1', data=form_data)
    assert response.status_code == 302
    assert target_location in response.location


def test_output_post(test_client, init_database, login):
    form_data = {
        'start_date': '2020-01-01',
        'end_date': '2020-01-02',
    }
    response = test_client.post('/output?page=1', data=form_data)
    assert response.status_code == 200


def test_output_post_invalid_form_no_redir(test_client, init_database, login):
    target_location = 'index'
    form_data = {
        'start_date': '2020-01-01',
        'end_date': '2020-01-02',
        'card_number': '1514fdf',
    }
    response = test_client.post('/output?page=1', data=form_data)
    assert response.status_code == 302
    assert target_location in response.location


def test_output_post_invalid_form_redir(test_client, init_database, login):
    form_data = {
        'start_date': '2020-01-01',
        'end_date': '2020-01-02',
        'card_number': '1514fdf',
    }
    response = test_client.post('/output?page=1', data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Field must be between 4 and 4 characters long.' in response.data


def test_output_post_empty_result_no_redir(test_client, init_database, login):
    target_location = 'index'
    form_data = {
        'start_date': '2020-03-01',
        'end_date': '2020-03-02',
    }
    response = test_client.post('/output?page=1', data=form_data)
    assert response.status_code == 302
    assert target_location in response.location


def test_output_post_empty_result_redir(test_client, init_database, login):
    form_data = {
        'start_date': '2020-03-01',
        'end_date': '2020-03-02',
    }
    response = test_client.post('/output?page=1', data=form_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Nothing found for' in response.data


def test_output_post_pages(test_client, init_database, login):
    form_data = {
        'start_date': '2020-01-01',
        'end_date': '2020-01-02',
    }
    response = test_client.post('/output?page=2', data=form_data)
    assert response.status_code == 200


def test_output_get_pages(test_client, init_database, login):
    response = test_client.get('/output?page=2')
    assert response.status_code == 200


def test_output_get_pages_out_of_range(test_client, init_database, login):
    response = test_client.get('/output?page=281')
    assert response.status_code == 404


def test_output_post_pages_out_of_range(test_client, init_database, login):
    form_data = {
        'start_date': '2020-01-01',
        'end_date': '2020-01-02',
    }
    response = test_client.post('/output?page=1281', data=form_data)
    assert response.status_code == 404


def test_output_get_pages_out_of_range_negative(test_client, init_database, login):
    response = test_client.get('/output?page=-3')
    assert response.status_code == 404


def test_output_post_pages_out_of_range_negative(test_client, init_database, login):
    form_data = {
        'start_date': '2020-01-01',
        'end_date': '2020-01-02',
    }
    response = test_client.post('/output?page=-3', data=form_data)
    assert response.status_code == 404


def test_output_get_no_pages(test_client, init_database, login):
    response = test_client.get('/output')
    assert response.status_code == 404


def test_output_post_no_pages(test_client, init_database, login):
    form_data = {
        'start_date': '2020-01-01',
        'end_date': '2020-01-02',
    }
    response = test_client.post('/output', data=form_data)
    assert response.status_code == 404


def test_download_get_no_login(test_client, init_database):
    response = test_client.get('/download?page=1')
    assert response.status_code == 302
    target_location = 'login'
    assert target_location in response.location


def test_download_get(test_client, init_database, login):
    response = test_client.get('/download?page=1')
    assert response.status_code == 200
    headers = b'merchant_name;city;address;phone_num;date;time;operation_type;pos_id;merchant_num;fin_service;card_number;card_holder'
    assert headers in response.data


def test_download_get_out_of_range(test_client, init_database, login):
    response = test_client.get('/download?page=345')
    assert response.status_code == 404


def test_download_post_no_login(test_client, init_database):
    response = test_client.post('/download?page=1')
    assert response.status_code == 405


def test_download_post(test_client, init_database, login):
    response = test_client.post('/download?page=1')
    assert response.status_code == 405
