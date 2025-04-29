from . import db
from flask_login import UserMixin

friends = db.Table(
    "friends",
    db.Column("user_id",   db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("friend_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    friends = db.relationship(
    "User",
    secondary=friends,
    primaryjoin=(friends.c.user_id    == id),
    secondaryjoin=(friends.c.friend_id == id),
    backref="friended_by",
    lazy="dynamic"
    )


class Expense(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    amount    = db.Column(db.Float,   nullable=False)
    category  = db.Column(db.String(64), nullable=False)
    date      = db.Column(db.Date,    nullable=False)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            "id":       self.id,
            "amount":   self.amount,
            "category": self.category,
            "date":     self.date.isoformat(),
        }