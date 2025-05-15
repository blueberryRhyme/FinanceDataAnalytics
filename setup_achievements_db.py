"""
Script to initialize the achievement system database tables 
and populate with initial achievements.
Run this once to set up the achievement system.
"""

from app import create_app, db
from app.models import Achievement, AchievementType, AchievementCategory
from config import Config

def setup_achievements_db():
    """Create database tables and seed initial achievements"""
    print("Setting up achievement system database...")
    
    # Create all tables defined in models
    db.create_all()
    
    # Check if achievements already exist
    if Achievement.query.first():
        print("Achievements already exist in the database. Skipping...")
        return
    
    # Define our achievements - keeping only the ones specifically requested
    achievements = [
        # First Step - track first transaction
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
        # Saving Star - track savings
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
        # Streak Keeper - track consecutive expenses
        Achievement(
            id=3,
            title='Streak Keeper',
            description='Log expenses for 7 consecutive days',
            type=AchievementType.CONSISTENCY,
            category=AchievementCategory.CONSISTENCY,
            icon='fa-solid fa-fire',
            points=30,
            criteria={"consecutive_days": 7}
        ),
        # Social Circle - track friend count
        Achievement(
            id=4,
            title='Social Circle',
            description='Add 5 friends to your network',
            type=AchievementType.SOCIAL,
            category=AchievementCategory.SOCIAL,
            icon='fa-solid fa-user-group',
            points=25,
            criteria={"friend_count": 5}
        ),
        # Income Champion - track income
        Achievement(
            id=5,
            title='Income Champion',
            description='Record $5,000 in income',
            type=AchievementType.MILESTONE,
            category=AchievementCategory.INCOME,
            icon='fa-solid fa-money-bill-wave',
            points=40,
            criteria={"income_amount": 5000}
        )
    ]
    
    # Add achievements to database
    for achievement in achievements:
        db.session.add(achievement)
    
    # Commit the changes
    db.session.commit()
    print(f"Added {len(achievements)} achievements to the database.")
    print("Achievement system setup complete!")


if __name__ == '__main__':
    app = create_app(Config)
    with app.app_context():
        setup_achievements_db()
