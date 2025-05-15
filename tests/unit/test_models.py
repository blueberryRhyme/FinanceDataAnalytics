import unittest
from datetime import date
from decimal import Decimal

from app import create_app
from app.models import (
    db,
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


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        # create app with testing config, and in-memory DB
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_and_settings_relationship(self):
        # create a user and its UserSettings
        u = User(username="alice", email="alice@example.com", password="hash")
        settings = UserSettings(monthly_budget=Decimal("1000.00"), currency="USD", timezone="UTC")
        u.settings = settings
        db.session.add(u)
        db.session.commit()

        # reload and check
        alice = User.query.filter_by(username="alice").one()
        self.assertIsNotNone(alice.settings)
        self.assertEqual(alice.settings.monthly_budget, Decimal("1000.00"))
        self.assertEqual(alice.settings.currency, "USD")

    def test_transactions_and_remaining_property(self):
        # create one user and two transactions
        u = User(username="bob", email="bob@example.com", password="hash")
        db.session.add(u)
        db.session.commit()

        tx = Transaction(
            user_id=u.id,
            date=date.today(),
            amount=Decimal("200.00"),
            category="food",
            type=TransactionType.expense,
        )
        db.session.add(tx)
        db.session.commit()

        # apply part of that transaction to a bill
        bill = Bill(created_by=u.id, description="Dinner", total=Decimal("200.00"))
        bt = BillTransaction(bill=bill, transaction=tx, amount_applied=Decimal("50.00"))
        db.session.add_all([bill, bt])
        db.session.commit()

        # remaining should be 150
        tx_refetched = db.session.get(Transaction, tx.id)
        self.assertAlmostEqual(tx_refetched.remaining, 150.00)

    def test_bill_and_members_settled_logic(self):
        # user and two members
        u1 = User(username="carl", email="carl@example.com", password="h")
        u2 = User(username="dan", email="dan@example.com", password="h")
        db.session.add_all([u1, u2])
        db.session.commit()

        # bill total 100
        bill = Bill(created_by=u1.id, description="Shared gift", total=Decimal("100.00"))
        # two members share 50 each
        m1 = BillMember(bill=bill, user=u1, share=Decimal("50.00"), paid=Decimal("50.00"))
        m2 = BillMember(bill=bill, user=u2, share=Decimal("50.00"), paid=Decimal("0.00"))
        db.session.add_all([bill, m1, m2])
        db.session.commit()

        # not yet settled because m2 hasn’t paid
        self.assertFalse(bill.settled)

        # now mark m2 paid
        m2.paid = Decimal("50.00")
        db.session.commit()
        self.assertTrue(bill.settled)

    def test_self_friending_and_transaction_friend(self):
        # create three users
        u1 = User(username="eve", email="eve@example.com", password="h")
        u2 = User(username="frank", email="frank@example.com", password="h")
        u3 = User(username="grace", email="grace@example.com", password="h")
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        # make friendships: eve ↔ frank
        u1.friends.append(u2)
        db.session.commit()
        # backref means frank.friended_by contains eve
        self.assertIn(u1, u2.friended_by)

        # link a transaction to a friend
        tx = Transaction(
            user_id=u1.id,
            date=date.today(),
            amount=Decimal("75.00"),
            category="coffee",
            type=TransactionType.expense,
        )
        db.session.add(tx)
        db.session.commit()

        tf = TransactionFriend(transaction_id=tx.id, friend_id=u2.id, confidence=0.85)
        db.session.add(tf)
        db.session.commit()

        # refetch and assert
        tf_refetched = TransactionFriend.query.first()
        self.assertEqual(tf_refetched.friend_id, u2.id)
        self.assertAlmostEqual(tf_refetched.confidence, 0.85)


if __name__ == "__main__":
    unittest.main()
