from app import create_app, db
from app.models import Goal, User
from flask import current_app

app = create_app()

with app.app_context():
    print("Checking goals database...")
    
    # Get all goals
    goals = Goal.query.all()
    print(f"Found {len(goals)} goals in database")
    
    # Print details of each goal
    for goal in goals:
        user = User.query.get(goal.user_id)
        username = user.username if user else "Unknown"
        print(f"Goal ID: {goal.id}, Title: {goal.title}, User: {username}, Public: {goal.is_public}")
    
    # Check if there's any issue with the user_goals relationship
    print("\nChecking user/goal relationships...")
    users = User.query.all()
    for user in users:
        user_goals = Goal.query.filter_by(user_id=user.id).all()
        print(f"User {user.username} has {len(user_goals)} goals")
