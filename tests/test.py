import unittest
from flask import Flask
from flask_testing import TestCase
from M3_Final_Project.app import app, db, User

class TestBankingApp(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True

    def create_app(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = self.SQLALCHEMY_DATABASE_URI
        app.config['TESTING'] = self.TESTING
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register_user(self):
        response = self.client.post('/register', data=dict(
            username='testuser',
            password='testpassword'
        ))
        self.assertEqual(response.status_code, 302)  # Redirects to home
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)

    def test_login_user(self):
        self.client.post('/register', data=dict(
            username='testuser',
            password='testpassword'
        ))
        response = self.client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login successful!', response.data)

    def test_deposit(self):
        self.client.post('/register', data=dict(
            username='testuser',
            password='testpassword'
        ))
        response = self.client.post('/deposit', data=dict(
            username='testuser',
            password='testpassword',
            amount='100.0'
        ))
        self.assertEqual(response.status_code, 302)
        user = User.query.filter_by(username='testuser').first()
        self.assertEqual(user.balance, 100.0)

    def test_withdraw(self):
        self.client.post('/register', data=dict(
            username='testuser',
            password='testpassword'
        ))
        self.client.post('/deposit', data=dict(
            username='testuser',
            password='testpassword',
            amount='100.0'
        ))
        response = self.client.post('/withdraw', data=dict(
            username='testuser',
            password='testpassword',
            amount='50.0'
        ))
        self.assertEqual(response.status_code, 302)
        user = User.query.filter_by(username='testuser').first()
        self.assertEqual(user.balance, 50.0)

    def test_withdraw_insufficient_funds(self):
        self.client.post('/register', data=dict(
            username='testuser',
            password='testpassword'
        ))
        self.client.post('/deposit', data=dict(
            username='testuser',
            password='testpassword',
            amount='50.0'
        ))
        response = self.client.post('/withdraw', data=dict(
            username='testuser',
            password='testpassword',
            amount='100.0'
        ))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Insufficient funds!', response.data)

    def test_balance(self):
        self.client.post('/register', data=dict(
            username='testuser',
            password='testpassword'
        ))
        self.client.post('/deposit', data=dict(
            username='testuser',
            password='testpassword',
            amount='100.0'
        ))
        response = self.client.post('/balance', data=dict(
            username='testuser',
            password='testpassword'
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"balance": 100.0', response.data)


if __name__ == '__main__':
    unittest.main()