import os
from typing import Dict, Union

import pytest

test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.py')
os.environ['FLASK_APPLICATION_SETTINGS'] = test_config_path
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

from flask_app.auth.models import User
from flask_app.auth import db

admin = {
    'username': 'admin',
    'email': 'admin@admin.ad',
    'password_hash': '123456',
    'is_verified': True,
    'is_active': True,
    'is_admin': True,
}
user1 = {
    'username': 'user1',
    'email': 'user1@user1.ad',
    'password_hash': '123456',
    'is_verified': True,
    'is_active': True,
    'is_admin': False,
}
user2 = {
    'username': 'user2',
    'email': 'user2@user2.ad',
    'password_hash': '123456',
    'is_verified': True,
    'is_active': False,
    'is_admin': False,
}
user3 = {
    'username': 'user3',
    'email': 'user3@user3.ad',
    'password_hash': '123456',
    'is_verified': False,
    'is_active': False,
    'is_admin': False,
}
users = (user1, user2, user3, admin)


@pytest.fixture(scope='module', autouse=True)
def init_users(init_database_auth):
    for user in users:
        user = User(**user)
        user.set_password(user.password_hash)
        db.session.add(user)
    db.session.commit()


@pytest.fixture(scope='class')
def login(test_client):
    def loginer(user: Dict[str, Union[str, bool]], redir: bool = False):
        form = {'username': user['username'], 'password': user['password_hash']}
        return test_client.post('/login', data=form, follow_redirects=redir)
    yield loginer
    print('logout')
    test_client.get('/logout')


class TestAdminPage:
    @pytest.fixture(scope='class')
    def admin_page(self, test_client):
        return test_client.get('/admin/')


class TestAdminGetNoLogin(TestAdminPage):
    def test_status_code(self, admin_page):
        assert admin_page.status_code == 302

    def test_location(self, admin_page):
        assert 'login' in admin_page.location


class TestAdminGetNoAdmin(TestAdminPage):
    @pytest.fixture(scope='class', autouse=True, params=[user1])
    def login_user(self, login, request):
        return login(request.param)

    def test_status_code(self, login_user, admin_page):
        assert admin_page.status_code == 302

    def test_location(self, login_user, admin_page):
        assert 'index' in admin_page.location


class TestAdminGetNotVerifiedOrApproved(TestAdminPage):
    @pytest.fixture(scope='class', autouse=True, params=[user3, user2])
    def login_user(self, login, request):
        return login(request.param)

    def test_status_code(self, login_user, admin_page):
        assert admin_page.status_code == 302

    def test_location(self, login_user, admin_page):
        assert 'login' in admin_page.location


class TestAdminGetAdmin(TestAdminPage):
    @pytest.fixture(scope='class', autouse=True, params=[admin])
    def login_user(self, login, request):
        return login(request.param)

    def test_status_code(self, admin_page):
        assert admin_page.status_code == 200

    def test_data(self, admin_page):
        assert b'Admin tools' in admin_page.data

    def test_count_users(self, admin_page):
        assert admin_page.data.decode('utf-8').count('no-gutters') == len(users) + 2

    def test_empty_form(self, admin_page):
        assert b'Add' in admin_page.data

    @pytest.mark.parametrize('username', [user['username'] for user in users])
    def test_check_usernames(self, admin_page, username):
        assert username in admin_page.data.decode('utf-8')


@pytest.fixture(scope='class')
def admin_post(test_client):
    def poster(form, params: str = ''):
        return test_client.post(
            '/admin/',
            data=form, query_string=params,
            follow_redirects=False
        )
    return poster


@pytest.fixture(scope='class')
def login_admin(login):
    print('login as admin')
    return login(admin)


@pytest.mark.usefixtures('login_admin')
class TestAdminPost(TestAdminPage):
    new_user = {
        'user_id': 11,
        'email': 'newmail@mail.ru',
        'username': 'test_user_name',
        'is_verified': True,
        'is_active': True,
        'is_admin': True,
        'password': '123456',
    }

    @pytest.fixture(scope='class')
    def change(self, admin_post):
        return admin_post(self.new_user)

    def test_status_code(self, change):
        assert change.status_code == 200

    def test_flash(self, change):
        data = change.data.decode('utf-8')
        with open('test_count_rows.html', 'w') as f:
            f.write(data)
        assert 'Change successful!' in data

    @pytest.mark.parametrize('data', (new_user['username'], new_user['email']))
    def test_data(self, change, data):
        assert data in change.data.decode('utf-8')

    def test_count_rows(self, change):
        data = change.data.decode('utf-8')
        with open('test_count_rows.html', 'w') as f:
            f.write(data)
        assert data.count('no-gutters') == len(users) + 3


@pytest.mark.usefixtures('login_admin')
class TestAdminIncorrectPost(TestAdminPage):
    new_user = {
        'user_id': 11,
        'email': 'newmail',
        'username': 'ttt',
    }

    @pytest.fixture(scope='class')
    def change(self, admin_post):
        users = User.query.filter_by(is_active=True).all()
        next_id = max(user.id for user in users) + 1
        self.new_user['id'] = next_id
        return admin_post(self.new_user)

    def test_status_code(self, change):
        assert change.status_code == 200

    def test_flash(self, change):
        assert b'Change successful!' not in change.data

    @pytest.mark.parametrize('data', (new_user['username'], new_user['email']))
    def test_data(self, change, data):
        assert data in change.data.decode('utf-8')

    def test_error_tags(self, change):
        error_tag = '<span style="color: red;">'
        data = change.data.decode('utf-8')
        assert data.count(error_tag) == 2


class TestDeleteGetNoAdmin(TestAdminPage):
    @pytest.fixture(scope='class', autouse=True, params=[user1])
    def login_user(self, login, request):
        return login(request.param)

    def test_status_code(self, login_user, admin_page):
        assert admin_page.status_code == 302

    def test_location(self, login_user, admin_page):
        assert 'index' in admin_page.location


class TestDeleteGetNotVerifiedOrApproved(TestAdminPage):
    @pytest.fixture(scope='class', autouse=True, params=[user3, user2])
    def login_user(self, login, request):
        return login(request.param)

    def test_status_code(self, login_user, admin_page):
        assert admin_page.status_code == 302

    def test_location(self, login_user, admin_page):
        assert 'login' in admin_page.location


@pytest.fixture(scope='class')
def admin_delete(test_client):
    def deleter(params: str = ''):
        return test_client.get(
            '/admin/delete',
            query_string=params,
            follow_redirects=True
        )
    return deleter


@pytest.mark.usefixtures('login_admin')
class TestDeletePost(TestAdminPage):
    @pytest.fixture(scope='class')
    def delete_result(self, admin_delete):
        return admin_delete({'id': 1})

    def test_status_code(self, delete_result):
        assert delete_result.status_code == 200

    def test_flash(self, delete_result):
        assert b'User test_user is deleted.' in delete_result.data

    def test_no_user_on_page(self, delete_result):
        data = delete_result.data.decode('utf-8')
        assert 'test_user@test.test' not in data

    def test_count_rows(self, delete_result):
        data = delete_result.data.decode('utf-8')
        assert data.count('no-gutters') == len(users) + 2


@pytest.mark.usefixtures('login_admin')
class TestDeletePostNoId(TestAdminPage):
    @pytest.fixture(scope='class')
    def delete_result(self, admin_delete):
        return admin_delete()

    def test_status_code(self, delete_result):
        assert delete_result.status_code == 200

    def test_flash(self, delete_result):
        assert b'User with id None does not exist' in delete_result.data

    def test_count_rows(self, delete_result):
        data = delete_result.data.decode('utf-8')
        assert data.count('no-gutters') == len(users) + 2


class TestMakeForms:
    def test_make_forms(self):
        pass
