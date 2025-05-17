import unittest
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Transaction, Bill
from config import TestConfig
from decimal import Decimal
from io import BytesIO
import json
import json


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

    def test_user_registration(self):
        resp = self.client.post(
            '/register',
            data={
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'Secret123',
                'confirm': 'Secret123',
            },
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Your account has been created!', resp.data)

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

    def test_logout_flow(self):
        # login first
        self.client.post(
            '/login',
            data={'email': 't@example.com', 'password': 'secret'},
            follow_redirects=True
        )

        # logout
        resp = self.client.post('/logout', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'You have been logged out.', resp.data)

        # attempt to access a protected route
        resp2 = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp2.status_code, 401)

    def test_profile_page(self):
        # log in first
        self.client.post('/login', data={
            'email': 't@example.com',
            'password': 'secret'
        }, follow_redirects=True)

        # access the profile page
        resp = self.client.get('/profile', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b't@example.com', resp.data)

    def test_transaction_creation(self):
        # log in first
        self.client.post('/login', data={
            'email': 't@example.com',
            'password': 'secret'
        }, follow_redirects=True)

        # create a transaction
        resp = self.client.post('/transactionForm', data={
            'date': '2025-05-14',
            'amount': '100.00',
            'description': 'Groceries',
            'type': 'expense',
            'category': 'food'
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Expense Recorded', resp.data)

        # verify transaction exists in the database
        with self.app.app_context():
            tx = Transaction.query.filter_by(description='Groceries').first()
            self.assertIsNotNone(tx)
            self.assertEqual(tx.amount, Decimal('100.00'))

    def test_csv_import(self):
        # log in first
        self.client.post('/login', data={
            'email': 't@example.com',
            'password': 'secret'
        }, follow_redirects=True)

        # simulate CSV upload
        data = {
            'csv_file': (BytesIO(b'date,amount,description\n14/05/2025,100.00,Groceries'), 'transactions.csv')
        }
        resp = self.client.post('/transactionForm', data=data, content_type='multipart/form-data', follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'CSV Processed', resp.data)

        # verify transaction exists in the database
        with self.app.app_context():
            tx = Transaction.query.filter_by(description='Groceries').first()
            self.assertIsNotNone(tx)
            self.assertEqual(tx.amount, Decimal('100.00'))

    def test_create_bill(self):
        # login
        self.client.post(
            '/login',
            data={'email': 't@example.com', 'password': 'secret'},
            follow_redirects=True
        )

        # create a bill
        resp = self.client.post(
            '/api/bill/create',
            json={
                'transaction_ids': [],
                'member_ids': [],
                'details': 'Test Bill'
            },
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn(b'bill_id', resp.data)

        # verify in DB
        data = json.loads(resp.data)
        bill_id = data['bill_id']

        with self.app.app_context():
            bill = db.session.get(Bill, bill_id)
            self.assertIsNotNone(bill)
            self.assertEqual(bill.description, 'Test Bill')

    def test_update_settings(self):
        # login
        self.client.post(
            '/login',
            data={'email': 't@example.com', 'password': 'secret'},
            follow_redirects=True
        )

        # update settings
        resp = self.client.post(
            '/api/update_settings',
            json={
                'currency': 'USD',
                'budget': 500.00
            },
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'USD', resp.data)
        self.assertIn(b'500.0', resp.data)

        # verify the settings were updated
        with self.app.app_context():
            user = User.query.filter_by(email='t@example.com').first()
            self.assertEqual(user.settings.currency, 'USD')
            self.assertEqual(user.settings.monthly_budget, Decimal('500.00'))
        

if __name__ == '__main__':
    unittest.main()
