import os
from unittest import TestCase

from flask import url_for

from flask_app import create_app
from flask_app.auth import db, models


test_config_path = os.path.join(os.path.dirname(__file__), 'test_config.py')
os.environ['FLASK_APPLICATION_SETTINGS'] = test_config_path


class TestUser:
    username: str = 'test_user'
    email: str = 'test@email.com'
    password: str = 'test_password'
    verified: bool = False
    admin_approved: bool = True
    is_active: bool = True

    @classmethod
    def to_dir(cls):
        return {
            'username': 'test_user',
            'email': 'test@email.com',
            'verified': False,
            'admin_approved': True,
            'is_active': True,
        }


class TestAuth(TestCase):
    def setUp(self):
        app = create_app()
        self._app = app
        with self._app.app_context():
            db.create_all()
            user = models.User(**TestUser.to_dir())
            user.set_password(TestUser.password)
            db.session.add(user)
            db.session.commit()
        self.app = app.test_client()

    def tearDown(self):
        url_logout = self.get_url('auth.logout')
        self.app.get(url_logout)
        with self._app.app_context():
            db.drop_all()

    def get_url(self, view: str, **kwargs):
        with self._app.test_request_context():
            return url_for(view, **kwargs)

    def login_(self, username: str, password: str, redir: bool = False, url: str = None):
        url = url or self.get_url('auth.login')
        form = {'username': username, 'password': password}
        response = self.app.post(
            url,
            content_type='application/x-www-form-urlencoded',
            data=form,
            follow_redirects=redir
        )
        return response

    def verify_user(self, username: str):
        with self._app.app_context():
            user = models.User.query.filter_by(username=TestUser.username).first()
            user.verified = True
            db.session.commit()


    def test_login_get(self):
        url = self.get_url('auth.login')
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign In', response.data)

    def test_login(self):
        url_location = self.get_url('views.index')
        self.verify_user(TestUser.username)
        response = self.login_(TestUser.username, TestUser.password)
        print(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(url_location), response.location)


    def test_login_logged_in(self):
        self.test_login()
        response = self.app.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You&#39;re already logged in!', response.data)

    def test_login_bad_form(self):
        response = self.login_('not', 'tes', True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Field must be between 4 and 64 characters long.', response.data)
        self.assertIn(b'Field must be between 4 and 128 characters long.', response.data)

    def test_login_bad_user_no_redir(self):
        response = self.login_('not_a_user', 'test')
        self.assertEqual(response.status_code, 200)

    def test_login_bad_user_redir(self):
        response = self.login_('not_a_user', 'test', True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_login_bad_pass_no_redir(self):
        response = self.login_(TestUser.username, 'test')
        self.assertEqual(response.status_code, 200)

    def test_login_bad_pass_redir(self):
        response = self.login_(TestUser.username, 'test', True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_login_not_verified(self):
        response = self.login_(TestUser.username, TestUser.password, True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email not verified, check your mailbox.', response.data)

    def test_login_index(self):
        url_location = self.get_url('views.index')
        url = self.get_url('auth.login') + '?next=%2Findex'
        self.verify_user(TestUser.username)
        response = self.login_(TestUser.username, TestUser.password, url=url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.location.endswith(url_location),
            f'{response.location} != {url_location}'
        )


    def test_logout(self):
        self.test_login()
        url_index = self.get_url('views.index')
        url_login = self.get_url('auth.login')
        url_logout = self.get_url('auth.logout')

        response1 = self.app.get(url_index)
        self.assertEqual(response1.status_code, 200)
        response2 = self.app.get(url_logout)
        self.assertEqual(response2.status_code, 302)
        self.assertTrue(response2.location.endswith(url_login), response2.location)
        response3 = self.app.get(url_index)
        self.assertEqual(response3.status_code, 302)
        self.assertEqual(response3.location, 'http://localhost/login?next=%2Findex')


    def register(
        self,
        username: str,
        email: str,
        password: str,
        password2: str,
        redir: bool = False
    ):
        url = self.get_url('auth.register')
        form = {
            'username': username,
            'password': password,
            'password2': password2,
            'email': email,
        }
        response = self.app.post(
            url,
            content_type='application/x-www-form-urlencoded',
            data=form,
            follow_redirects=redir
        )
        return response

    def test_register_get(self):
        url = self.get_url('auth.register')
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)

    def test_register(self):
        url_location = self.get_url('auth.login')
        response = self.register('new_user', 'new_user@email.com', '1234', '1234')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(url_location), response.location)

    def test_register_logged_in(self):
        self.test_login()
        url = self.get_url('auth.register')
        response = self.app.get(url, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You&#39;re already registered!', response.data)

    def test_register_invalid_form(self):
        response = self.register('123', 'new_user@email.com', '123', '123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Field must be between 4 and 64 characters long.', response.data)
        self.assertIn(b'Field must be between 4 and 128 characters long.', response.data)

    def test_register_same_username(self):
        response = self.register(TestUser.username, 'new_user@email.com', '123', '123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please use a different username.', response.data)

    def test_register_same_email(self):
        response = self.register('new_user', TestUser.email, '123', '123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please use a different email address.', response.data)

    def test_register_not_mathcing_pass(self):
        response = self.register('new_user', 'new_user@email.com', '1234', '12345')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Field must be equal to password.', response.data)


    def reset_password_request(self, email: str, redir: bool = False):
        url = self.get_url('auth.reset_password_request')
        form = {'email': email, }
        response = self.app.post(
            url,
            content_type='application/x-www-form-urlencoded',
            data=form,
            follow_redirects=redir
        )
        return response

    def test_reset_password_request_get(self):
        url = self.get_url('auth.reset_password_request')
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn(b'Request Reset Password', response.data)

    def test_reset_password_request(self):
        url_location = self.get_url('auth.login')
        response = self.reset_password_request(TestUser.email)
        self.assertEqual(response.status_code, 302, response.data)
        info = f'{response.location}\n{response.data}'
        self.assertTrue(response.location.endswith(url_location), info)

    def test_reset_password_request_redir(self):
        response = self.reset_password_request(TestUser.email, True)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn(b'Check your email', response.data)

    def test_reset_password_request_logged_in(self):
        self.test_login()
        url = self.get_url('auth.reset_password_request')
        response = self.app.get(url, follow_redirects=True)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn(b'You&#39;re already logged in!', response.data)

    def test_reset_password_request_invalid_form(self):
        response = self.reset_password_request('123')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn(b'Invalid email address.', response.data)


    def reset_password_get(self, token: str, redir: bool = False):
        url = self.get_url('auth.reset_password', token=token)
        return self.app.get(url, follow_redirects=redir)

    def get_password_token(self, username: str):
        with self._app.app_context():
            user = models.User.query.filter_by(username=username).first()
            return user.get_reset_password_token()

    def reset_password(
        self,
        token: str,
        password: str,
        password2: str,
        redir: bool = False
    ):
        url = self.get_url('auth.reset_password', token=token)
        form = {
            'password': password,
            'password2': password2,
        }
        response = self.app.post(
            url,
            content_type='application/x-www-form-urlencoded',
            data=form,
            follow_redirects=redir
        )
        return response

    def test_reset_password_get_empty(self):
        response = self.reset_password_get('')
        self.assertEqual(response.status_code, 404, response.data)

    def test_reset_password_get_bad_token(self):
        url_location = self.get_url('views.index')
        response = self.reset_password_get('123')
        self.assertEqual(response.status_code, 302, response.data)
        self.assertTrue(response.location.endswith(url_location), response.location)

    def test_reset_password_get_bad_token_redir(self):
        response = self.reset_password_get('123', True)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn(b'Bad reset password token.', response.data)

    def test_reset_password_get(self):
        token = self.get_password_token(TestUser.username)
        response = self.reset_password_get(token)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn(b'Reset Your Password', response.data)

    def test_reset_password(self):
        url_location = self.get_url('auth.login')
        token = self.get_password_token(TestUser.username)
        response = self.reset_password(token, '123456', '123456')
        TestUser.password = '123456'
        self.assertEqual(response.status_code, 302, response.data)
        self.assertTrue(response.location.endswith(url_location), response.location)

# TODO: Check fro is_active and admin_approved
