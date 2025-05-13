import unittest
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User
from config import TestConfig


class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # create a test user with a hashed password
            u = User(username='test', email='t@example.com')
            u.password = generate_password_hash('secret')
            db.session.add(u)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_index_requires_login(self):
        # hitting a protected endpoint without login should give 401
        resp = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp.status_code, 401)

    def test_login_flow(self):
        # login with correct creds
        resp = self.client.post('/login',
            data={'email': 't@example.com', 'password': 'secret'},
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Dashboard', resp.data)


if __name__ == '__main__':
    unittest.main()
