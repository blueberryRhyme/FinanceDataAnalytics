"""
Model tests with achievement hooks disabled to prevent test interference.

The application has SQLAlchemy event listeners in achievement_hooks.py that trigger actions when 
models are inserted into the database. These hooks cause problems in the test environment:
- There are after_insert hooks for both Transaction and Bill models
- When a transaction or bill is created in tests, these hooks run check_achievements
- This causes unexpected behavior in the test environment, including potential object deletion
"""

import unittest
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


class IsolatedTestConfig(TestConfig):
    """Test config that disables achievement hooks and other side effects"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    DISABLE_ACHIEVEMENT_HOOKS = True  # Prevents achievement hooks from running during tests


class IsolatedModelTestCase(unittest.TestCase):
    def setUp(self):
        # Create app with testing config that disables hooks
        self.app = create_app(IsolatedTestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables in the in-memory database
        db.create_all()

    def tearDown(self):
        # Clean up resources
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

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
        
        # Create transaction
        tx = Transaction(
            user_id=user.id,
            date=date.today(),
            amount=Decimal("75.50"),
            category="groceries",
            type=TransactionType.expense,
            description="Weekly shopping"
        )
        db.session.add(tx)
        db.session.commit()
        
        # Retrieve and verify
        tx_id = tx.id
        db.session.expunge_all()  # Clear session
        
        # Get transaction from database
        retrieved_tx = Transaction.query.get(tx_id)
        self.assertIsNotNone(retrieved_tx)
        self.assertEqual(retrieved_tx.amount, Decimal("75.50"))
        self.assertEqual(retrieved_tx.description, "Weekly shopping")


    def test_bill_creation(self):
        """Test basic Bill creation"""
        # Create a user
        user = User(username="bill_creator", email="bill@example.com", password="password")
        db.session.add(user)
        db.session.commit()
        
        # Create a bill
        bill = Bill(
            created_by=user.id,
            description="Test Bill",
            date=date.today(),
            total=Decimal("100.00")
        )
        db.session.add(bill)
        db.session.commit()
        
        # Verify bill was saved
        bill_id = bill.id
        db.session.expunge_all()  # Clear session
        
        # Retrieve bill
        retrieved_bill = db.session.get(Bill, bill_id)
        self.assertIsNotNone(retrieved_bill)
        self.assertEqual(retrieved_bill.total, Decimal("100.00"))
        self.assertEqual(retrieved_bill.description, "Test Bill")
    
    def test_bill_members(self):
        """Test Bill with members"""
        # Step 1: Create users first
        user1 = User(username="member1", email="member1@example.com", password="password")
        user2 = User(username="member2", email="member2@example.com", password="password")
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # Store user IDs for later use
        user1_id = user1.id
        user2_id = user2.id
        
        # Step 2: Create a bill
        bill = Bill(
            created_by=user1_id,  # Reference by ID to avoid detached object issues
            description="Shared Dinner",
            date=date.today(),
            total=Decimal("80.00")
        )
        db.session.add(bill)
        db.session.commit()
        
        bill_id = bill.id
        
        # Step 3: Add bill members using IDs rather than objects
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
        
        # Clean up connections between sessions
        db.session.close()
        
        # Step 4: Retrieve and verify bill
        retrieved_bill = db.session.get(Bill, bill_id)
        self.assertIsNotNone(retrieved_bill)
        self.assertEqual(len(retrieved_bill.members), 2)
        
        # Test settled property - should be false since one member hasn't paid
        self.assertFalse(retrieved_bill.settled)
        
        # Step 5: Update member2 payment status
        # Find member2 by user_id instead of relying on the loop order
        member2_id = None
        for member in retrieved_bill.members:
            if member.user_id == user2_id:
                member.paid = Decimal("40.00")  # Now user2 pays their share
                member2_id = member.id
                break
                
        self.assertIsNotNone(member2_id, "Couldn't find member2 in bill members")
        db.session.commit()
        
        # Step 6: Get a fresh copy of the bill to check if it's settled
        # Clear session first to ensure fresh data
        db.session.close()
        fresh_bill = db.session.get(Bill, bill_id)
        
        # Now the bill should be settled
        self.assertTrue(fresh_bill.settled, "Bill should be settled after all members paid")
    
    def test_transaction_bill_relationship(self):
        """Test Transaction and Bill relationship through BillTransaction"""
        # Step 1: Create user and save ID
        user = User(username="tx_bill_user", email="txbill@example.com", password="password")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
        # Step 2: Create a transaction with user_id
        tx = Transaction(
            user_id=user_id,  # Use ID instead of object reference
            date=date.today(),
            amount=Decimal("150.00"),
            category="restaurant",
            type=TransactionType.expense,
            description="Dinner expense"
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id
        
        # Step 3: Create a bill
        bill = Bill(
            created_by=user_id,  # Use ID instead of object reference
            description="Group Dinner",
            date=date.today(),
            total=Decimal("100.00")
        )
        db.session.add(bill)
        db.session.commit()
        bill_id = bill.id
        
        # Step 4: Link the transaction to the bill
        # Only applying part of the transaction amount to this bill
        bt = BillTransaction(
            bill_id=bill_id,  # Use ID instead of object reference
            transaction_id=tx_id,  # Use ID instead of object reference
            amount_applied=Decimal("75.00")
        )
        db.session.add(bt)
        db.session.commit()
        
        # Clean session
        db.session.close()
        
        # Step 5: Get a fresh copy of the transaction and verify remaining amount
        retrieved_tx = db.session.get(Transaction, tx_id)
        # 150.00 - 75.00 = 75.00 remaining
        self.assertAlmostEqual(retrieved_tx.remaining, 75.00)
        
        # Step 6: Add another bill using the same transaction
        bill2 = Bill(
            created_by=user_id,  # Use ID instead of object reference
            description="Second Bill",
            date=date.today(),
            total=Decimal("50.00")
        )
        db.session.add(bill2)
        db.session.commit()
        bill2_id = bill2.id
        
        # Step 7: Create another bill transaction link
        bt2 = BillTransaction(
            bill_id=bill2_id,  # Use ID instead of object reference
            transaction_id=tx_id,  # Use ID instead of object reference
            amount_applied=Decimal("50.00")
        )
        db.session.add(bt2)
        db.session.commit()
        
        # Clean session again
        db.session.close()
        
        # Step 8: Get a fresh copy of the transaction to verify final remaining amount
        fresh_tx = db.session.get(Transaction, tx_id)
        # 150.00 - 75.00 - 50.00 = 25.00 remaining
        self.assertAlmostEqual(fresh_tx.remaining, 25.00, 
                               msg="Transaction remaining amount should be 25.00 after applying to two bills")
    
    def test_friendship(self):
        """Test user friendship relationships"""
        user1 = User(username="friend1", email="friend1@example.com", password="password")
        user2 = User(username="friend2", email="friend2@example.com", password="password")
        db.session.add_all([user1, user2])
        db.session.commit()
        
        user1_id = user1.id
        user2_id = user2.id
        
        # Add friendship
        user1.friends.append(user2)
        db.session.commit()
        
        # Close and reopen session to avoid detached instance errors
        db.session.close()
        
        # Get fresh copies of the users
        fresh_user1 = db.session.get(User, user1_id)
        fresh_user2 = db.session.get(User, user2_id)
        
        # Check that user2 is in user1's friends list
        friends = list(fresh_user1.friends)
        self.assertEqual(len(friends), 1)
        self.assertEqual(friends[0].username, "friend2")
        
        # Check the reverse relationship with friended_by
        friended_by = list(fresh_user2.friended_by)
        self.assertEqual(len(friended_by), 1)
        self.assertEqual(friended_by[0].username, "friend1")
    
    def test_transaction_friend(self):
        """Test TransactionFriend association"""
        # Create users
        user1 = User(username="tx_owner", email="txowner@example.com", password="password")
        user2 = User(username="tx_friend", email="txfriend@example.com", password="password")
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # Create a transaction
        tx = Transaction(
            user_id=user1.id,
            date=date.today(),
            amount=Decimal("35.00"),
            category="entertainment",
            type=TransactionType.expense,
            description="Movies with friend"
        )
        db.session.add(tx)
        db.session.commit()
        
        tx_id = tx.id
        user2_id = user2.id
        
        # Create transaction friend association
        tf = TransactionFriend(
            transaction_id=tx_id,
            friend_id=user2_id,
            confidence=0.95
        )
        db.session.add(tf)
        db.session.commit()
        
        # Close session to avoid detached object issues
        db.session.close()
        
        # Verify the association with a fresh query
        retrieved_tf = TransactionFriend.query.filter_by(transaction_id=tx_id).first()
        self.assertIsNotNone(retrieved_tf)
        self.assertEqual(retrieved_tf.friend_id, user2_id)
        self.assertAlmostEqual(retrieved_tf.confidence, 0.95)


if __name__ == "__main__":
    unittest.main()
