from sqlalchemy.sql import func
from . import db
from flask_login import UserMixin
import enum

friends_table = db.Table(
    "friends",
    db.Column("user_id",   db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("friend_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)



class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email    = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


    settings  = db.relationship(
        'UserSettings',
        uselist=False,
        back_populates='user',
        cascade='all, delete-orphan'
    )

    transactions = db.relationship(
        'Transaction',
        back_populates='user',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    friends = db.relationship(
        "User",
        secondary=friends_table,
        primaryjoin=(friends_table.c.user_id    == id),
        secondaryjoin=(friends_table.c.friend_id == id),
        backref="friended_by",
        lazy="dynamic"
    )

    

class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    user_id         = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True
    )
    monthly_budget = db.Column(db.Numeric(10,2), nullable=False, default=0.00)
    currency       = db.Column(db.String(3), nullable=False, default='AUD')
    timezone       = db.Column(db.String(50), nullable=False, default='Australia/Perth')

    user            = db.relationship(
        'User',
        back_populates='settings',
        uselist=False
    )


class TransactionType(enum.Enum):
    expense  = 'expense'
    income   = 'income'
    transfer = 'transfer'


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id                 = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )
    date               = db.Column(db.Date, nullable=False)
    amount             = db.Column(db.Numeric(10, 2), nullable=False)  # always stored positive
    category           = db.Column(db.String, nullable=False)
    type               = db.Column(
        db.Enum(TransactionType, name='tx_type'),
        nullable=False
    )
    transfer_direction = db.Column(db.Enum('in','out', name='transfer_dir'), nullable=True)

    description        = db.Column(db.String(255), nullable=True)

    user               = db.relationship(
        'User',
        back_populates='transactions'
    )

class BillTransaction(db.Model):
    __tablename__ = 'bill_transaction'
    id             = db.Column(db.Integer, primary_key=True)
    bill_id        = db.Column(db.Integer, db.ForeignKey('bill.id', ondelete='CASCADE'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False)
    amount_applied = db.Column(db.Numeric(12,2), nullable=False)

    bill        = db.relationship('Bill', back_populates='transactions')
    transaction = db.relationship('Transaction')
    

class Bill(db.Model):
    __tablename__ = "bill"
    
    transactions = db.relationship(
        'BillTransaction',
        back_populates='bill',
        cascade='all, delete-orphan'
    )

    id           = db.Column(db.Integer, primary_key=True)
    created_by   = db.Column(db.Integer,
                             db.ForeignKey("users.id", ondelete="CASCADE"),
                             nullable=False)
    description  = db.Column(db.String(255))
    date         = db.Column(db.Date, default=func.current_date(), nullable=False)
    total        = db.Column(db.Numeric(12, 2), nullable=False)
    settled      = db.Column(db.Boolean, default=False)

    members = db.relationship(
        "BillMember",
        back_populates="bill",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class BillMember(db.Model):
    __tablename__ = "bill_member"

    id        = db.Column(db.Integer, primary_key=True)
    bill_id   = db.Column(db.Integer,
                          db.ForeignKey("bill.id", ondelete="CASCADE"),
                          nullable=False)
    user_id   = db.Column(db.Integer,
                          db.ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False)
    share     = db.Column(db.Numeric(12, 2), nullable=False)     # “what I owe”
    paid      = db.Column(db.Numeric(12, 2), default=0)          # “what I have paid”
    settled   = db.Column(db.Boolean, default=False)

    bill  = db.relationship("Bill", back_populates="members")
    user  = db.relationship("User")

class TransactionFriend(db.Model):
    """
    1-to-N link between an existing Transaction and friends it’s associated to.
    Confidence stores the similarity score shown to the user for transparency.
    """
    __tablename__ = "transaction_friend"

    id             = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer,
                               db.ForeignKey("transactions.id", ondelete="CASCADE"),
                               nullable=False)
    friend_id      = db.Column(db.Integer,
                               db.ForeignKey("users.id", ondelete="CASCADE"),
                               nullable=False)
    confidence     = db.Column(db.Float, default=1.0)