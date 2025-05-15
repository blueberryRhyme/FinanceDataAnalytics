"""
Achievement Engine for FinShare
This module handles detecting when users have earned achievements
and awarding them accordingly.
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
from app.models import User, Transaction, TransactionType, Achievement, UserAchievement
from app.models import AchievementType, AchievementCategory
from app import db

# Dictionary mapping achievement IDs to their check functions
ACHIEVEMENT_CHECKS = {}


def register_achievement_check(achievement_id):
    """Decorator to register an achievement check function"""
    def decorator(func):
        ACHIEVEMENT_CHECKS[achievement_id] = func
        return func
    return decorator


def check_achievements(user_id, context=None):
    """
    Check all applicable achievements for a user
    
    Args:
        user_id: ID of the user to check achievements for
        context: Optional dictionary with context about what triggered the check
                (e.g. {'transaction': new_transaction} for transaction-related events)
    
    Returns:
        List of newly earned achievements
    """
    user = User.query.get(user_id)
    if not user:
        return []
    
    # Get all achievements
    all_achievements = Achievement.query.all()
    
    # Get user's already earned achievements to exclude them
    earned_achievement_ids = set(
        ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=user_id).all()
    )
    
    newly_earned = []
    
    # Check each achievement
    for achievement in all_achievements:
        # Skip already earned achievements
        if achievement.id in earned_achievement_ids:
            continue
            
        # Get the check function
        check_func = ACHIEVEMENT_CHECKS.get(achievement.id)
        if check_func:
            # Check if achievement is earned or get progress
            result = check_func(user, achievement, context)
            
            if isinstance(result, bool) and result:
                # Achievement earned
                newly_earned.append(award_achievement(user, achievement))
            elif isinstance(result, float) and 0 < result < 1:
                # Update progress
                update_achievement_progress(user, achievement, result)
    
    return newly_earned


def award_achievement(user, achievement):
    """
    Award an achievement to a user
    
    Args:
        user: User object
        achievement: Achievement object
    
    Returns:
        UserAchievement object
    """
    # Check if user already has this achievement
    existing = UserAchievement.query.filter_by(
        user_id=user.id,
        achievement_id=achievement.id
    ).first()
    
    if existing:
        # Update progress if needed
        if existing.progress < 100:
            existing.progress = 100
            existing.earned_date = datetime.utcnow()
            db.session.commit()
        return existing
    
    # Create new achievement record
    user_achievement = UserAchievement(
        user_id=user.id,
        achievement_id=achievement.id,
        earned_date=datetime.utcnow(),
        is_public=True,  # Default to public
        progress=100  # Fully completed
    )
    db.session.add(user_achievement)
    db.session.commit()
    return user_achievement


def update_achievement_progress(user, achievement, progress):
    """
    Update progress for an in-progress achievement
    
    Args:
        user: User object
        achievement: Achievement object
        progress: Float between 0 and 1 representing completion percentage
    
    Returns:
        UserAchievement object or None if no record exists yet
    """
    # Check if we already have a progress record
    user_achievement = UserAchievement.query.filter_by(
        user_id=user.id,
        achievement_id=achievement.id
    ).first()
    
    progress_percent = min(round(progress * 100, 1), 99.9)  # Cap at 99.9% until earned
    
    if user_achievement:
        # Update existing record if new progress is higher
        if progress_percent > user_achievement.progress:
            user_achievement.progress = progress_percent
            db.session.commit()
        return user_achievement
    else:
        # Create new progress record
        user_achievement = UserAchievement(
            user_id=user.id,
            achievement_id=achievement.id,
            earned_date=None,  # No earned date yet
            is_public=True,  # Default to public
            progress=progress_percent
        )
        db.session.add(user_achievement)
        db.session.commit()
        return user_achievement


# Example achievement check functions
@register_achievement_check(1)
def check_first_transaction(user, achievement, context):
    """Check if user has logged their first transaction"""
    transaction_count = Transaction.query.filter_by(user_id=user.id).count()
    return transaction_count > 0


@register_achievement_check(2)
def check_savings_milestone_1000(user, achievement, context):
    """Check if user has saved $1000 total"""
    # Count both income transactions and refunds as savings
    total_savings = db.session.query(func.sum(Transaction.amount)).\
        filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.income
        ).scalar() or 0
    
    # Also add refunds (they should be income with category 'refund')
    refund_savings = db.session.query(func.sum(Transaction.amount)).\
        filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.income,
            Transaction.category == 'refund'
        ).scalar() or 0
    
    # Also count any transactions specifically marked as savings
    savings_category = db.session.query(func.sum(Transaction.amount)).\
        filter(
            Transaction.user_id == user.id,
            Transaction.category == 'savings'
        ).scalar() or 0
    
    # Total up all savings types
    total = float(total_savings) + float(refund_savings) + float(savings_category)
        
    # Check if they've reached the milestone
    if total >= 1000:
        return True
    
    # Otherwise return progress
    return total / 1000


@register_achievement_check(3)
def check_expense_streak(user, achievement, context):
    """Check if user has logged expenses for 7 consecutive days"""
    today = datetime.utcnow().date()
    streak_days = 7  # Required streak length
    
    # Get distinct dates with transactions, ordered by date
    dates_with_transactions = db.session.query(Transaction.date).\
        filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.expense,
            Transaction.date >= today - timedelta(days=streak_days + 3)  # Extra days to check streak
        ).distinct().order_by(desc(Transaction.date)).all()
    
    # Extract just the dates
    transaction_dates = set(d[0] for d in dates_with_transactions)
    
    # Count consecutive days
    current_streak = 0
    for i in range(streak_days):
        check_date = today - timedelta(days=i)
        if check_date in transaction_dates:
            current_streak += 1
        else:
            break
    
    # Check if they've achieved the streak
    if current_streak >= streak_days:
        return True
    
    # Otherwise return progress
    return current_streak / streak_days


@register_achievement_check(4)
def check_friend_count(user, achievement, context):
    """Check if user has added at least 5 friends"""
    friend_count = user.friends.count()
    required_friends = 5
    
    if friend_count >= required_friends:
        return True
    
    return friend_count / required_friends


@register_achievement_check(5)
def check_income_champion(user, achievement, context):
    """Check if user has recorded $5,000 in income"""
    # Calculate total income from all income transactions
    total_income = db.session.query(func.sum(Transaction.amount)).\
        filter(
            Transaction.user_id == user.id,
            Transaction.type == TransactionType.income
        ).scalar() or 0
    
    target_income = 5000
    
    # Check if they've reached the milestone
    if float(total_income) >= target_income:
        return True
    
    # Otherwise return progress percentage
    return float(total_income) / target_income
