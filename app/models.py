from . import db
from flask_login import UserMixin

friends = db.Table(
    "friends",
    db.Column("user_id",   db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("friend_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    expenses = db.relationship('Expense', back_populates='user', lazy='dynamic')



class Expense(db.Model):
    __tablename__ = 'expenses'
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date     = db.Column(db.Date,   nullable=False)
    amount   = db.Column(db.Float,  nullable=False)
    category = db.Column(db.String(50), nullable=False)

    user = db.relationship('User', back_populates='expenses')

