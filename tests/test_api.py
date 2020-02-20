import os
import unittest
import json
from typing import Any

from flask import url_for

test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.py')
os.environ['FLASK_APPLICATION_SETTINGS'] = test_config_path

from flask_app import create_app
import tests.slip_obj as slip_obj


API_URL = 'http://127.0.0.1:5000/api/slips'
PASSWORD = {'password': 'SecurityFlaw'}


class TestAPI(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.config['TESTING'] = True
        app.config['JSON_AS_ASCII'] = False
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = True
        self.app = app
        self.client = self.app.test_client()

    def tearDown(self):
        objects = (el for el in dir(slip_obj) if not el.endswith('__'))
        for element in objects:
            slip = getattr(slip_obj, element)
            url = API_URL + f'/{slip["date"]}/{slip["ref_num"]}'
            response = self.client.delete(url, query_string=PASSWORD)

    def get_url(self, view: str):
        with self.app.test_request_context():
            return url_for(view)

    def post_slips(self, data: Any = [], params: str = '',):
        return self.client.post(API_URL, json=data, query_string=params)


class TestGetSlips(TestAPI):
    def get_slips(self, params: str = ''):
        response = self.client.get(API_URL, query_string=params)
        return response

    fixture = {
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
        (200, 232): [
            {'date': ['2020-01-01'], 'page_id': 0},
            {'date': ['2020-01-01', '2020-01-01'], 'page_id': 0}
        ],
        (200, 4): [
            {'date': ['2020-01-01'], 'object_code': 'NE07'},
            {'date': ['2020-01-01'], 'pos_id': '25613123'}
        ],
        (200, 10): [{'date': ['2020-01-01', '2020-02-01'], 'per_page': 10}],
        (200, 1582): [{'date': ['2019-12-31', '2020-01-01'], 'page_id': 0}],
        (200, 0): [
            {'date': ['2015-01-01', ]},
            {'date': ['2029-01-01', ]},
            {'date': ['2020-01-01', ], 'pos_id': 12345},
        ],
    }

    def test_get_slips(self):
        for (status_code, data_len), params in self.fixture.items():
            for param in params:
                response = self.get_slips(param)
                data = json.loads(response.data)
                info = f'get {param} expect {(status_code, data_len)}, got {data}'
                self.assertEqual(response.status_code, status_code, info)
                if data_len is not None:
                    self.assertEqual(len(data['data']), data_len, info)


class TestPostSlips(TestAPI):
    fixture = {
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

    def test_post_slips(self):
        for result, params in self.fixture.items():
            for param in params:
                response = self.post_slips(**param)
                data = json.loads(response.data)
                info = f'post {param} expect {result}, got {data}'
                self.assertEqual(response.status_code, result, info)

    def test_post_slips_not_unique(self):
        self.post_slips(data=[slip_obj.slip], params=PASSWORD)
        response = self.post_slips(data=[slip_obj.slip], params=PASSWORD)
        self.assertEqual(response.status_code, 409, response.data)

    def test_post_slips_some_of_many(self):
        response = self.post_slips(
            data=[slip_obj.slip, slip_obj.slip, slip_obj.slip2],
            params=PASSWORD
        )
        data = response.data
        self.assertEqual(response.status_code, 201, data)
        self.assertIn(b'Added 2 slips out of 3', data, data)


class TestGetSlip(TestAPI):
    def get_slip(self, date: str = '', ref_num: str = ''):
        url = API_URL + f'/{date}/{ref_num}'
        return self.client.get(url)

    def test_get_slip(self):
        self.post_slips(data=[slip_obj.slip], params=PASSWORD)

        response = self.get_slip(slip_obj.slip['date'], slip_obj.slip['ref_num'])
        self.assertEqual(response.status_code, 200, response.data)

        self.maxDiff = None
        slip_new = json.loads(response.data)
        slip_new.pop('something')
        slip_old = {**slip_obj.slip}
        self.assertEqual(slip_new, slip_old)

    def test_get_slip_no_result(self):
        response = self.get_slip(slip_obj.slip['date'], slip_obj.slip['ref_num'])
        self.assertEqual(response.status_code, 404, response.data)


class TestUpdateSlip(TestAPI):
    def update_slip(
        self,
        date: str = '',
        ref_num: str = '',
        data: Any = [],
        params: str = ''
    ):
        url = API_URL + f'/{date}/{ref_num}'
        return self.client.put(url, json=data, query_string=params)

    def test_update_slip(self):
        self.post_slips(data=[slip_obj.slip], params=PASSWORD)

        new_slip = {
            **slip_obj.slip,
            'file_link': slip_obj.slip['file_link'].replace('1', '2')
        }
        response = self.update_slip(
            slip_obj.slip['date'],
            slip_obj.slip['ref_num'],
            new_slip,
            PASSWORD
        )
        self.assertEqual(response.status_code, 201, response.data)

    def test_update_slip_bad_rrn(self):
        response = self.update_slip(
            slip_obj.slip['date'],
            slip_obj.slip['ref_num'],
            slip_obj.slip,
            PASSWORD
        )
        self.assertEqual(response.status_code, 201, response.data)

    def test_update_slip_not_unique(self):
        self.post_slips(data=[slip_obj.slip, slip_obj.slip2], params=PASSWORD)

        new_slip = {
            **slip_obj.slip,
            'file_link': slip_obj.slip2['file_link']
        }
        response = self.update_slip(
            slip_obj.slip['date'],
            slip_obj.slip['ref_num'],
            new_slip,
            PASSWORD
        )
        self.assertEqual(response.status_code, 409, response.data)


class TestDeleteSlip(TestAPI):
    def delete_slip(self, date: str = '', ref_num: str = '', params: str = ''):
        url = API_URL + f'/{date}/{ref_num}'
        return self.client.delete(url, query_string=params)

    def test_delete_slip(self):
        self.post_slips([slip_obj.slip], PASSWORD)

        response = self.delete_slip(
            slip_obj.slip['date'],
            slip_obj.slip['ref_num'],
            PASSWORD
        )
        self.assertEqual(response.status_code, 204, response.data)

    def test_delete_no_slip(self):
        response = self.delete_slip(
            slip_obj.slip['date'],
            slip_obj.slip['ref_num'],
            PASSWORD
        )
        self.assertEqual(response.status_code, 404, response.data)

    def test_delete_no_password(self):
        response = self.delete_slip(
            slip_obj.slip['date'],
            slip_obj.slip['ref_num']
        )
        self.assertEqual(response.status_code, 400, response.data)

    def test_delete_bad_password(self):
        response = self.delete_slip(
            slip_obj.slip['date'],
            slip_obj.slip['ref_num'],
            {'password': 'vodka'}
        )
        self.assertEqual(response.status_code, 401, response.data)
