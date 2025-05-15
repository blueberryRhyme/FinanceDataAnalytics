"""
Seed script to populate the database with initial achievements.
Run this after setting up the database schema to populate achievements.
"""

from app import db, create_app
from app.models import Achievement, AchievementType, AchievementCategory
from config import Config

def seed_achievements():
    """Create initial set of achievements in the database"""
    # Delete any existing achievements first (for re-seeding)
    Achievement.query.delete()
    
    # Define our achievements
    achievements = [
        # Milestone achievements
        Achievement(
            id=1,
            title='First Step',
            description='Log your first financial transaction',
            type=AchievementType.MILESTONE,
            category=AchievementCategory.CONSISTENCY,
            icon='fa-solid fa-shoe-prints',
            points=10,
            criteria={"transaction_count": 1}
        ),
        Achievement(
            id=2,
            title='Saving Star',
            description='Save your first $1,000',
            type=AchievementType.MILESTONE,
            category=AchievementCategory.SAVINGS,
            icon='fa-solid fa-star',
            points=50,
            criteria={"savings_amount": 1000}
        ),
        Achievement(
            id=3,
            title='Streak Keeper',
            description='Log expenses for 7 consecutive days',
            type=AchievementType.STREAK,
            category=AchievementCategory.CONSISTENCY,
            icon='fa-solid fa-calendar-check',
            points=30,
            criteria={"streak_days": 7, "type": "expense"}
        ),
        Achievement(
            id=4,
            title='Social Circle',
            description='Add 5 friends to your network',
            type=AchievementType.SOCIAL,
            category=AchievementCategory.SOCIAL,
            icon='fa-solid fa-users',
            points=25,
            criteria={"friend_count": 5}
        ),
        Achievement(
            id=5,
            title='Budget Master',
            description='Stay under budget for a full month',
            type=AchievementType.BUDGET,
            category=AchievementCategory.BUDGETING,
            icon='fa-solid fa-piggy-bank',
            points=40,
            criteria={"under_budget": True, "days_in_month": 28}
        ),
        Achievement(
            id=6,
            title='Expense Tracker',
            description='Log 50 expenses',
            type=AchievementType.MILESTONE,
            category=AchievementCategory.EXPENSE_MANAGEMENT,
            icon='fa-solid fa-receipt',
            points=20,
            criteria={"expense_count": 50}
        ),
        Achievement(
            id=7,
            title='Income Champion',
            description='Record $5,000 in income',
            type=AchievementType.MILESTONE,
            category=AchievementCategory.INCOME,
            icon='fa-solid fa-trophy',
            points=35,
            criteria={"income_amount": 5000}
        ),
        Achievement(
            id=8,
            title='Bill Splitter',
            description='Split your first bill with friends',
            type=AchievementType.SPECIAL,
            category=AchievementCategory.SOCIAL,
            icon='fa-solid fa-money-bill-split',
            points=15,
            criteria={"split_bill_count": 1}
        ),
        Achievement(
            id=9,
            title='Savings Rate Hero',
            description='Maintain a 20% savings rate for 3 months',
            type=AchievementType.SAVINGS_RATE,
            category=AchievementCategory.SAVINGS,
            icon='fa-solid fa-hand-holding-dollar',
            points=60,
            criteria={"savings_rate": 0.2, "months": 3}
        ),
        Achievement(
            id=10,
            title='Financial Forecaster',
            description='Use the forecast feature 5 times',
            type=AchievementType.MILESTONE,
            category=AchievementCategory.BUDGETING,
            icon='fa-solid fa-chart-line',
            points=20,
            criteria={"forecast_count": 5}
        ),
    ]
    
    # Add achievements to database
    for achievement in achievements:
        db.session.add(achievement)
    
    # Commit the changes
    db.session.commit()
    print(f"Added {len(achievements)} achievements to the database.")


if __name__ == '__main__':
    app = create_app(Config)
    with app.app_context():
        seed_achievements()
