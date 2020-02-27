import json
import os
from typing import Any

import pytest

import tests.slip_obj as slip_obj


test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.py')
os.environ['FLASK_APPLICATION_SETTINGS'] = test_config_path
API_URL = 'http://127.0.0.1:5000/api/slips'
PASSWORD = {'password': 'SecurityFlaw'}


@pytest.fixture(scope='function')
def post_slips(test_client):
    def poster(data: Any = [], params: str = ''):
        return test_client.post(API_URL, json=data, query_string=params)
    yield poster
    for slip in slip_obj.slips:
        url = f'{API_URL}/{slip["date"]}/{slip["ref_num"]}'
        test_client.delete(url, query_string=PASSWORD)


@pytest.fixture
def get_slips(test_client):
    def getter(params: str = ''):
        return test_client.get(API_URL, query_string=params)
    return getter


@pytest.fixture
def get_slip(test_client):
    def getter(date: str = '', ref_num: str = ''):
        url = f'{API_URL}/{date}/{ref_num}'
        return test_client.get(url)
    return getter


@pytest.fixture
def update_slip(test_client):
    def updater(date: str = '', ref_num: str = '', data: Any = [], params: str = ''):
        url = f'{API_URL}/{date}/{ref_num}'
        return test_client.put(url, json=data, query_string=params)
    return updater


@pytest.fixture
def delete_slip(test_client):
    def deleter(date: str = '', ref_num: str = '', params: str = ''):
        url = API_URL + f'/{date}/{ref_num}'
        return test_client.delete(url, query_string=params)

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
    # (200, 232): [
    #     {'date': ['2020-01-01'], 'page_id': 0},
    #     {'date': ['2020-01-01', '2020-01-01'], 'page_id': 0}
    # ],
    # (200, 4): [
    #     {'date': ['2020-01-01'], 'object_code': 'NE07'},
    #     {'date': ['2020-01-01'], 'pos_id': '25613123'}
    # ],
    (200, 10): [{'date': ['2020-01-01', '2020-02-01'], 'per_page': 10}],
    # (200, 1582): [{'date': ['2019-12-31', '2020-01-01'], 'page_id': 0}],
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
        response = get_slips(param)
        data = json.loads(response.data)
        info = f'get {param} expect {(status_code, data_len)}, got {data}'
        assert response.status_code == status_code, info
        if data_len is not None:
            assert len(data['data']) == data_len, info


fixture_post = {
    400: [
        {},
        {'data': [slip_obj.slip]},
        {'params': PASSWORD, 'data': []},
    ],
    401: [
        {'data': [slip_obj.slip], 'params': {'password': 'vodka'}}
    ],
    201: [
        {'params': PASSWORD, 'data': [slip_obj.slip]},
        {
            'params': PASSWORD,
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
        response = post_slips(**param)
        data = json.loads(response.data)
        info = f'post {param} expect {result}, got {data}'
        assert response.status_code == result, info


def test_post_slips_not_unique(post_slips):
    post_slips(data=[slip_obj.slip], params=PASSWORD)
    response = post_slips(data=[slip_obj.slip], params=PASSWORD)
    assert response.status_code == 409, response.data


def test_post_slips_some_of_many(post_slips):
    response = post_slips(
        data=[slip_obj.slip, slip_obj.slip, slip_obj.slip2],
        params=PASSWORD
    )
    data = response.data
    assert response.status_code == 201, data
    assert b'Added 2 slips out of 3' in data, data


def test_get_slip(get_slip, post_slips):
    post_slips(data=[slip_obj.slip], params=PASSWORD)

    response = get_slip(slip_obj.slip['date'], slip_obj.slip['ref_num'])
    assert response.status_code == 200, response.data

    slip_from_response = json.loads(response.data)
    slip_from_response.pop('something')
    assert slip_from_response == slip_obj.slip


def test_get_slip_no_result(get_slip):
    response = get_slip(slip_obj.slip['date'], slip_obj.slip['ref_num'])
    assert response.status_code == 404, response.data


def test_update_slip(update_slip, post_slips):
    post_slips(data=[slip_obj.slip], params=PASSWORD)

    new_slip = {
        **slip_obj.slip,
        'file_link': slip_obj.slip['file_link'].replace('1', '2')
    }
    response = update_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        new_slip,
        PASSWORD
    )
    assert response.status_code == 201, response.data


def test_update_slip_bad_rrn(update_slip):
    response = update_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        slip_obj.slip,
        PASSWORD
    )
    assert response.status_code == 201, response.data


def test_update_slip_not_unique(post_slips, update_slip):
    post_slips(data=[slip_obj.slip, slip_obj.slip2], params=PASSWORD)

    new_slip = {
        **slip_obj.slip,
        'file_link': slip_obj.slip2['file_link']
    }
    response = update_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        new_slip,
        PASSWORD
    )
    assert response.status_code == 409, response.data


def test_delete_slip(post_slips, delete_slip):
    post_slips([slip_obj.slip], PASSWORD)

    response = delete_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        PASSWORD
    )
    assert response.status_code == 204, response.data


def test_delete_no_slip(delete_slip):
    response = delete_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        PASSWORD
    )
    assert response.status_code == 404, response.data


def test_delete_no_password(delete_slip):
    response = delete_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num']
    )
    assert response.status_code == 400, response.data


def test_delete_bad_password(delete_slip):
    response = delete_slip(
        slip_obj.slip['date'],
        slip_obj.slip['ref_num'],
        {'password': 'vodka'}
    )
    assert response.status_code == 401, response.data
