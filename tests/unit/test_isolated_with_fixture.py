"""
Model tests that work with global pytest fixtures and disable achievement hooks.

This version is designed to work well when run alongside other tests.
"""

import unittest
import pytest
from datetime import date
from decimal import Decimal
import os

from app import create_app, db
from app.models import (
    User,
    UserSettings,
    Transaction,
    TransactionType,
    Bill,
    BillTransaction,
    BillMember,
    TransactionFriend,
)
from config import TestConfig


class StrictlyIsolatedTestConfig(TestConfig):
    """Test config that disables achievement hooks and ensures isolation"""
    TESTING = True
    # Use a unique URI for each test run to prevent cross-contamination
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    DISABLE_ACHIEVEMENT_HOOKS = True


@pytest.fixture(scope="function")
def app_context():
    """Create a fresh application context for each test."""
    app = create_app(StrictlyIsolatedTestConfig)
    with app.app_context() as ctx:
        db.create_all()
        yield ctx
        db.session.remove()
        db.drop_all()


class IsolatedModelTestCase(unittest.TestCase):
    
    @pytest.fixture(autouse=True)
    def setup_with_context(self, app_context):
        """Set up test with app context fixture."""
        self.app_context = app_context
        
    # Helper method for creating test users
    def create_test_users(self, count=1):
        """Create one or more test users and return their IDs"""
        users = []
        for i in range(count):
            user = User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                password="password"
            )
            db.session.add(user)
        
        db.session.commit()
        return [user.id for user in User.query.all()[:count]]
    
    def test_user_creation(self):
        """Test that we can create and retrieve a user"""
        user = User(username="testuser", email="test@example.com", password="password")
        db.session.add(user)
        db.session.commit()
        
        # Check user was saved
        retrieved = User.query.filter_by(username="testuser").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.email, "test@example.com")
    
    def test_user_settings(self):
        """Test user settings relationship"""
        user = User(username="alice", email="alice@example.com", password="password")
        settings = UserSettings(monthly_budget=Decimal("1000.00"), currency="USD", timezone="UTC")
        user.settings = settings
        
        db.session.add(user)
        db.session.commit()
        
        # Retrieve and verify
        alice = User.query.filter_by(username="alice").first()
        self.assertIsNotNone(alice.settings)
        self.assertEqual(alice.settings.monthly_budget, Decimal("1000.00"))
        self.assertEqual(alice.settings.currency, "USD")
    
    def test_transaction_basics(self):
        """Test basic transaction creation without bill relationships"""
        # Create a user
        user = User(username="bob", email="bob@example.com", password="password")
        db.session.add(user)
        db.session.commit()
        
        user_id = user.id
        
        # Create transaction
        tx = Transaction(
            user_id=user_id,
            date=date.today(),
            amount=Decimal("75.50"),
            category="groceries",
            type=TransactionType.expense,
            description="Weekly shopping"
        )
        db.session.add(tx)
        db.session.commit()
        
        # Get transaction from database
        tx_id = tx.id
        db.session.close()
        
        retrieved_tx = db.session.get(Transaction, tx_id)
        self.assertIsNotNone(retrieved_tx)
        self.assertEqual(retrieved_tx.amount, Decimal("75.50"))
        self.assertEqual(retrieved_tx.description, "Weekly shopping")
    
    def test_bill_creation(self):
        """Test basic Bill creation"""
        # Create a user
        user = User(username="bill_creator", email="bill@example.com", password="password")
        db.session.add(user)
        db.session.commit()
        
        user_id = user.id
        
        # Create a bill
        bill = Bill(
            created_by=user_id,
            description="Test Bill",
            date=date.today(),
            total=Decimal("100.00")
        )
        db.session.add(bill)
        db.session.commit()
        
        # Retrieve bill
        bill_id = bill.id
        db.session.close()
        
        retrieved_bill = db.session.get(Bill, bill_id)
        self.assertIsNotNone(retrieved_bill)
        self.assertEqual(retrieved_bill.total, Decimal("100.00"))
        self.assertEqual(retrieved_bill.description, "Test Bill")


    def test_bill_members(self):
        """Test Bill with members"""
        # Step 1: Create users first
        user_ids = self.create_test_users(2)  # Create 2 users
        user1_id, user2_id = user_ids
        
        # Step 2: Create a bill
        bill = Bill(
            created_by=user1_id,
            description="Shared Dinner",
            date=date.today(),
            total=Decimal("80.00")
        )
        db.session.add(bill)
        db.session.commit()
        bill_id = bill.id
        
        # Step 3: Add bill members
        member1 = BillMember(
            bill_id=bill_id,
            user_id=user1_id,
            share=Decimal("40.00"),
            paid=Decimal("80.00")  # User1 paid the full amount
        )
        member2 = BillMember(
            bill_id=bill_id,
            user_id=user2_id,
            share=Decimal("40.00"),
            paid=Decimal("0.00")   # User2 hasn't paid yet
        )
        db.session.add_all([member1, member2])
        db.session.commit()
        
        # Step 4: Retrieve and verify bill
        db.session.close()
        retrieved_bill = db.session.get(Bill, bill_id)
        self.assertIsNotNone(retrieved_bill)
        self.assertEqual(len(retrieved_bill.members), 2)
        
        # Test settled property - should be false since one member hasn't paid
        self.assertFalse(retrieved_bill.settled)
        
        # Step 5: Update member2 payment status
        # Find member2 by user_id
        member2_id = None
        for member in retrieved_bill.members:
            if member.user_id == user2_id:
                member.paid = Decimal("40.00")
                member2_id = member.id
                break
                
        self.assertIsNotNone(member2_id, "Couldn't find member2 in bill members")
        db.session.commit()
        
        # Step 6: Get a fresh bill to check if it's settled
        db.session.close()
        fresh_bill = db.session.get(Bill, bill_id)
        
        # Now the bill should be settled
        self.assertTrue(fresh_bill.settled, "Bill should be settled after all members paid")

    def test_transaction_bill_relationship(self):
        """Test Transaction and Bill relationship through BillTransaction"""
        # Step 1: Create user
        user_id = self.create_test_users(1)[0]
        
        # Step 2: Create transaction
        tx = Transaction(
            user_id=user_id,
            date=date.today(),
            amount=Decimal("150.00"),
            category="restaurant",
            type=TransactionType.expense,
            description="Dinner expense"
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id
        
        # Step 3: Create bill
        bill = Bill(
            created_by=user_id,
            description="Group Dinner",
            date=date.today(),
            total=Decimal("100.00")
        )
        db.session.add(bill)
        db.session.commit()
        bill_id = bill.id
        
        # Step 4: Link transaction to bill
        bt = BillTransaction(
            bill_id=bill_id,
            transaction_id=tx_id,
            amount_applied=Decimal("75.00")
        )
        db.session.add(bt)
        db.session.commit()
        
        # Step 5: Verify remaining amount
        db.session.close()
        retrieved_tx = db.session.get(Transaction, tx_id)
        # 150.00 - 75.00 = 75.00 remaining
        self.assertAlmostEqual(retrieved_tx.remaining, 75.00)
        
        # Step 6: Add another bill
        bill2 = Bill(
            created_by=user_id,
            description="Second Bill",
            date=date.today(),
            total=Decimal("50.00")
        )
        db.session.add(bill2)
        db.session.commit()
        bill2_id = bill2.id
        
        # Step 7: Link transaction to second bill
        bt2 = BillTransaction(
            bill_id=bill2_id,
            transaction_id=tx_id,
            amount_applied=Decimal("50.00")
        )
        db.session.add(bt2)
        db.session.commit()
        
        # Step 8: Check final remaining amount
        db.session.close()
        fresh_tx = db.session.get(Transaction, tx_id)
        # 150.00 - 75.00 - 50.00 = 25.00 remaining
        self.assertAlmostEqual(fresh_tx.remaining, 25.00, 
                               msg="Transaction remaining amount should be 25.00 after applying to two bills")
    
    def test_friendship(self):
        """Test user friendship relationships"""
        # Create users
        user_ids = self.create_test_users(2)
        user1_id, user2_id = user_ids
        
        # Get user objects
        user1 = db.session.get(User, user1_id)
        user2 = db.session.get(User, user2_id)
        
        # Add friendship
        user1.friends.append(user2)
        db.session.commit()
        
        # Close session for clean state
        db.session.close()
        
        # Get fresh copies
        fresh_user1 = db.session.get(User, user1_id)
        fresh_user2 = db.session.get(User, user2_id)
        
        # Check friendship relationships
        friends = list(fresh_user1.friends)
        self.assertEqual(len(friends), 1)
        self.assertEqual(friends[0].id, user2_id)
        
        friended_by = list(fresh_user2.friended_by)
        self.assertEqual(len(friended_by), 1)
        self.assertEqual(friended_by[0].id, user1_id)
    
    def test_transaction_friend(self):
        """Test TransactionFriend association"""
        # Create users
        user_ids = self.create_test_users(2)
        user1_id, user2_id = user_ids
        
        # Create transaction
        tx = Transaction(
            user_id=user1_id,
            date=date.today(),
            amount=Decimal("35.00"),
            category="entertainment",
            type=TransactionType.expense,
            description="Movies with friend"
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id
        
        # Create transaction friend association
        tf = TransactionFriend(
            transaction_id=tx_id,
            friend_id=user2_id,
            confidence=0.95
        )
        db.session.add(tf)
        db.session.commit()
        
        # Close session
        db.session.close()
        
        # Verify association
        retrieved_tf = TransactionFriend.query.filter_by(transaction_id=tx_id).first()
        self.assertIsNotNone(retrieved_tf)
        self.assertEqual(retrieved_tf.friend_id, user2_id)
        self.assertAlmostEqual(retrieved_tf.confidence, 0.95)
