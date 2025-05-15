from sqlalchemy.sql import func
from . import db
from flask_login import UserMixin
import enum
from datetime import datetime

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
    bill_transactions = db.relationship('BillTransaction',
                                        back_populates='transaction')
    @property
    def remaining(self):
        # sum up everything that’s been applied across *all* bills
        applied = sum(bt.amount_applied for bt in self.bill_transactions)
        return float(self.amount) - float(applied)


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

    @property
    def settled(self):
        return all(bm.paid >= bm.share for bm in self.members)
    
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


# Achievement System Models
class AchievementType(enum.Enum):
    """Types of achievements that can be earned"""
    MILESTONE = 'milestone'      # Reaching a financial milestone (save $1000, etc)
    STREAK = 'streak'            # Consistent behavior (log transactions for 7 days)
    SAVINGS_RATE = 'savings'     # Achievement related to savings percentage
    BUDGET = 'budget'            # Staying under budget achievements
    SOCIAL = 'social'            # Social activity achievements (adding friends, etc)
    SPECIAL = 'special'          # Special one-time achievements


class AchievementCategory(enum.Enum):
    """Categories for grouping achievements"""
    SAVINGS = 'savings'
    EXPENSE_MANAGEMENT = 'expense'
    INCOME = 'income'
    BUDGETING = 'budget'
    SOCIAL = 'social'
    CONSISTENCY = 'consistency'


class Achievement(db.Model):
    """Model for achievement definitions"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum(AchievementType), nullable=False)
    category = db.Column(db.Enum(AchievementCategory), nullable=False)
    icon = db.Column(db.String(100), nullable=False)  # CSS class or URL
    points = db.Column(db.Integer, default=10)  # Points earned for gamification
    criteria = db.Column(db.JSON, nullable=False)  # JSON data for achievement criteria
    
    # Relationship to earned achievements
    users = db.relationship('UserAchievement', back_populates='achievement')
    
    def __repr__(self):
        return f'<Achievement {self.title}>'


class UserAchievement(db.Model):
    """Model to track which achievements users have earned"""
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False)
    earned_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_public = db.Column(db.Boolean, default=True)  # Whether this achievement is visible to friends
    progress = db.Column(db.Float, default=100)  # Percent complete (default 100% for earned)
    
    # Relationships - removed direct user relationship to avoid conflict
    achievement = db.relationship('Achievement', back_populates='users')
    interactions = db.relationship('AchievementInteraction', back_populates='user_achievement', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UserAchievement user_id={self.user_id} - {self.achievement.title}>'


class InteractionType(enum.Enum):
    """Types of interactions for achievement posts"""
    LIKE = 'like'
    COMMENT = 'comment'


class AchievementInteraction(db.Model):
    """Model to store likes and comments on achievements"""
    __tablename__ = 'achievement_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_achievement_id = db.Column(db.Integer, db.ForeignKey('user_achievements.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)  # User who interacted
    interaction_type = db.Column(db.Enum(InteractionType), nullable=False)
    content = db.Column(db.Text, nullable=True)  # NULL for likes, text for comments
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    interacting_user = db.relationship('User', foreign_keys=[user_id])  # User who performed the interaction
    user_achievement = db.relationship('UserAchievement', back_populates='interactions')
    
    def __repr__(self):
        return f'<AchievementInteraction {self.user.username} - {self.interaction_type.value}>'


# Update User model to include achievements
User.achievements = db.relationship(
    'UserAchievement',
    foreign_keys=[UserAchievement.user_id],
    primaryjoin=(User.id == UserAchievement.user_id),
    lazy='dynamic',
    cascade='all, delete-orphan'
)