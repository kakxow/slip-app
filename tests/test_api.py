import base64
import json
import os
from typing import Any

import pytest

import tests.slip_obj as slip_obj


test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.py')
os.environ['FLASK_APPLICATION_SETTINGS'] = test_config_path
API_URL = 'http://127.0.0.1:5000/api/slips'
HEADERS = {'Authorization': f'Basic {base64.b64encode(b"user:password").decode("utf-8")}'}


@pytest.fixture(scope='function')
def post_slips(test_client, init_database):
    def poster(data: Any = None, params: str = '', headers: dict = None):
        headers = headers or {}
        data = data or []
        return test_client.post(API_URL, json=data, query_string=params, headers=headers)
    yield poster
    for slip in slip_obj.slips:
        url = f'{API_URL}/{slip["date"]}/{slip["ref_num"]}'
        test_client.delete(url, headers=HEADERS)


@pytest.fixture
def get_slips(test_client, init_database):
    def getter(params: str = '', headers: dict = None):
        headers = headers or {}
        return test_client.get(API_URL, query_string=params, headers=headers)
    return getter


@pytest.fixture
def get_slip(test_client, init_database):
    def getter(date: str = '', ref_num: str = '', headers: dict = None):
        url = f'{API_URL}/{date}/{ref_num}'
        headers = headers or {}
        return test_client.get(url, headers=headers)
    return getter


@pytest.fixture
def update_slip(test_client, init_database):
    def updater(date: str = '', ref_num: str = '', data: Any = None, params: str = '', headers: dict = None):
        headers = headers or {}
        data = data or []
        url = f'{API_URL}/{date}/{ref_num}'
        return test_client.put(url, json=data, query_string=params, headers=headers)
    return updater


@pytest.fixture
def delete_slip(test_client, init_database):
    def deleter(date: str = '', ref_num: str = '', params: str = '', headers: dict = None):
        headers = headers or {}
        url = API_URL + f'/{date}/{ref_num}'
        return test_client.delete(url, query_string=params, headers=headers)

    return deleter


fixture_get = {
    (400, None): [
        '',
        {'date': ['2020-01-01'], 'page_id': -15},
        {'date': ['2020-01-01'], 'per_page': -15},
        {'date': ['2020-01-01'], 'per_page': 0},
        {'per_page': 1},
        {'date': ['2020-01-01'], 'some': 'args'},
    ],
    (404, None): [{'date': ['2020-01-01'], 'page_id': 999}],
    (200, 20): [
        {'date': ['2020-01-01'], 'page_id': 1},
        {'date': ['2020-01-01']},
        {'date': ['2020-01-01', '2020-01-02']},
    ],
    (200, 30): [{'date': ['2020-01-01'], 'page_id': 1, 'per_page': 30}],
    (200, 10): [{'date': ['2020-01-01', '2020-02-01'], 'per_page': 10}],
    (200, 0): [
        {'date': ['2015-01-01', ]},
        {'date': ['2029-01-01', ]},
        {'date': ['2020-01-01', ], 'pos_id': 12345},
    ],
}


@pytest.mark.parametrize('result, params', fixture_get.items())
def test_get_slips(get_slips, result, params):
    status_code, data_len = result
    for param in params:
        response = get_slips(param, headers=HEADERS)
        data = json.loads(response.data)
        info = f'get {param} expect {(status_code, data_len)}, got {data}'
        assert response.status_code == status_code, info
        if data_len is not None:
            assert len(data['data']) == data_len, info


def test_get_slips_no_auth(get_slips):
    param = fixture_get[(200, 20)][0]
    response = get_slips(param)
    assert response.status_code == 401, json.loads(response.data)


def test_get_slips_bad_auth(get_slips):
    param = fixture_get[(200, 20)][0]
    headers = {'Authorization': f'Basic {base64.b64encode(b"user:fdfsa")}'}
    response = get_slips(param, headers=headers)
    assert response.status_code == 401, json.loads(response.data)


fixture_post = {
    400: [
        {},
        {'params': {'random_param': 'random'}, 'data': []},
        {'data': []},
    ],
    201: [
        {'data': [slip_obj.slip]},
        {
            'data': [
                slip_obj.slip,
                slip_obj.slip2,
                slip_obj.slip3
            ],
        }
    ]
}


@pytest.mark.parametrize('result, params', fixture_post.items())
def test_post_slips(post_slips, result, params):
    for param in params:
        response = post_slips(**param, headers=HEADERS)
        data = json.loads(response.data)
        info = f'post {param} expect {result}, got {data}'
        assert response.status_code == result, info


def test_post_slips_no_auth(post_slips):
    param = fixture_post[201][0]
    response = post_slips(**param)
    assert response.status_code == 401, json.loads(response.data)


def test_post_slips_bad_auth(post_slips):
    param = fixture_post[201][0]
    headers = {'Authorization': f'Basic {base64.b64encode(b"user:fdfsa")}'}
    response = post_slips(**param, headers=headers)
    assert response.status_code == 401, json.loads(response.data)


def test_post_slips_not_unique(post_slips):
    post_slips(data=[slip_obj.slip], headers=HEADERS)
    response = post_slips(data=[slip_obj.slip], headers=HEADERS)
    assert response.status_code == 409, response.data


def test_post_slips_some_of_many(post_slips):
    response = post_slips(
        data=[slip_obj.slip, slip_obj.slip, slip_obj.slip2],
        headers=HEADERS
    )
    data = response.data
    assert response.status_code == 201, data
    assert b'Added 2 slips out of 3' in data, data


def test_get_slip(get_slip, post_slips):
    post_slips(data=[slip_obj.slip], headers=HEADERS)

    response = get_slip(slip_obj.slip['date'], slip_obj.slip['ref_num'], headers=HEADERS)
    assert response.status_code == 200, response.data

    slip_from_response = json.loads(response.data)
    slip_from_response.pop('something')
    assert slip_from_response == slip_obj.slip


def test_get_slip_no_auth(get_slip, post_slips):
    post_slips(data=[slip_obj.slip], headers=HEADERS)

    response = get_slip(slip_obj.slip['date'], slip_obj.slip['ref_num'])
    assert response.status_code == 401, response.data


def test_get_slip_no_result(get_slip):
    response = get_slip(slip_obj.slip['date'], slip_obj.slip['ref_num'], headers=HEADERS)
    assert response.status_code == 404, response.data


def test_update_slip(update_slip, post_slips):
    post_slips(data=[slip_obj.slip], headers=HEADERS)

    new_slip = {
        **slip_obj.slip,
        'file_link': slip_obj.slip['file_link'].replace('1', '2')
    }
    response = update_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        new_slip,
        headers=HEADERS
    )
    assert response.status_code == 201, response.data


def test_update_slip_no_auth(update_slip, post_slips):
    post_slips(data=[slip_obj.slip], headers=HEADERS)

    new_slip = {
        **slip_obj.slip,
        'file_link': slip_obj.slip['file_link'].replace('1', '2')
    }
    response = update_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        new_slip
    )
    assert response.status_code == 401, response.data


def test_update_slip_bad_rrn(update_slip):
    response = update_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        slip_obj.slip,
        headers=HEADERS
    )
    assert response.status_code == 201, response.data


def test_update_slip_not_unique(post_slips, update_slip):
    post_slips(data=[slip_obj.slip, slip_obj.slip2], headers=HEADERS)

    new_slip = {
        **slip_obj.slip,
        'file_link': slip_obj.slip2['file_link']
    }
    response = update_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        new_slip,
        headers=HEADERS
    )
    assert response.status_code == 409, response.data


def test_delete_slip(post_slips, delete_slip):
    post_slips([slip_obj.slip], headers=HEADERS)

    response = delete_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        headers=HEADERS
    )
    assert response.status_code == 204, response.data


def test_delete_slip_no_auth(post_slips, delete_slip):
    post_slips([slip_obj.slip], headers=HEADERS)

    response = delete_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num']
    )
    assert response.status_code == 401, response.data


def test_delete_no_slip(delete_slip):
    response = delete_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        headers=HEADERS
    )
    assert response.status_code == 404, response.data


def test_delete_bad_auth(delete_slip):
    response = delete_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        headers={'Authorization': f'Basic {base64.b64encode(b"user:fdfsa")}'}
    )
    assert response.status_code == 401, response.data
