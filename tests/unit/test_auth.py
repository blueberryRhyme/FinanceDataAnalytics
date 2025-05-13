import unittest
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from app import create_app, db
from app.models import User
from config import TestConfig


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_register_success(self):
        before = User.query.count()

        resp = self.client.post(
            '/register',
            data={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'Secret123',
                'confirm': 'Secret123',
            },
            follow_redirects=False
        )
        # redirect to /login
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

        after = User.query.count()
        self.assertEqual(after, before + 1)

        u = User.query.filter_by(username='newuser').one()
        # password hashing
        self.assertNotEqual(u.password, 'Secret123')
        self.assertTrue(check_password_hash(u.password, 'Secret123'))

        # default settings
        self.assertIsNotNone(u.settings)
        self.assertEqual(u.settings.currency, 'AUD')
        self.assertEqual(u.settings.monthly_budget, Decimal('0.00'))

    def test_register_validation_errors(self):
        resp = self.client.post(
            '/register',
            data={
                'username': '',
                'email': 'nope',
                'password': 'x',
                'confirm': 'y',
            },
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'This field is required.', resp.data)
        self.assertIn(b'Invalid email address.', resp.data)

    def test_login_success(self):
        u = User(username='tester', email='tester@example.com')
        u.password = generate_password_hash('letmein')
        db.session.add(u)
        db.session.commit()

        resp = self.client.post(
            '/login',
            data={'email': 'tester@example.com', 'password': 'letmein'},
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Dashboard', resp.data)

    def test_login_failure(self):
        u = User(username='tester2', email='tester2@example.com')
        u.password = generate_password_hash('rightpass')
        db.session.add(u)
        db.session.commit()

        resp = self.client.post(
            '/login',
            data={'email': 'tester2@example.com', 'password': 'wrongpass'},
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Login failed. Check your email and password.', resp.data)

    def test_protected_route_requires_login(self):
        resp = self.client.get('/dashboard', follow_redirects=False)
        # you return 401 on unauthorized
        self.assertEqual(resp.status_code, 401)

    def test_logout(self):
        u = User(username='logoutuser', email='logout@example.com')
        u.password = generate_password_hash('logoutpass')
        db.session.add(u)
        db.session.commit()

        # login
        self.client.post(
            '/login',
            data={'email': 'logout@example.com', 'password': 'logoutpass'},
            follow_redirects=True
        )

        # now logout via POST
        resp = self.client.post('/logout', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        # your template shows "You have been logged out."
        self.assertIn(b'You have been logged out.', resp.data)

        # protected route again
        resp2 = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp2.status_code, 401)


if __name__ == '__main__':
    unittest.main()
