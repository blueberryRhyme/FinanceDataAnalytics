"""
Debug script for the Goals feature
This will help diagnose why goals aren't appearing in both profile and community pages
"""
from app import create_app, db
from app.models import Goal, User, GoalInteraction, GoalInteractionType
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    print("==== GOAL SYSTEM DIAGNOSTICS ====")
    
    # Check if tables exist
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Database tables: {tables}")
    
    if 'goals' not in tables:
        print("ERROR: Goals table not found in database!")
    else:
        print("SUCCESS: Goals table exists")
    
    # Check if there are any goals in the database
    goals = Goal.query.all()
    print(f"Found {len(goals)} goals in database")
    
    # Print all users
    users = User.query.all()
    print(f"Found {len(users)} users in database")
    
    for user in users:
        print(f"User {user.id}: {user.username}")
        
    # Print all goals with details
    if goals:
        print("\nEXISTING GOALS:")
        for goal in goals:
            user = User.query.get(goal.user_id)
            username = user.username if user else "Unknown"
            print(f"Goal {goal.id}: '{goal.title}' by {username} (User ID: {goal.user_id})")
            print(f"  Target: ${goal.target_amount}, Current: ${goal.current_amount}")
            print(f"  Public: {goal.is_public}, Created: {goal.created_at}")
    else:
        print("\nNo existing goals found.")
        
    # Create a test goal if none exist
    if not goals:
        print("\nCreating a test goal...")
        # Find the first user
        test_user = User.query.first()
        if test_user:
            new_goal = Goal(
                user_id=test_user.id,
                title="Test Financial Goal",
                description="This is a test goal created by the debug script",
                target_amount=1000.00,
                current_amount=250.00,
                target_date=datetime.now() + timedelta(days=30),
                is_public=True
            )
            db.session.add(new_goal)
            db.session.commit()
            print(f"Created test goal: '{new_goal.title}' for user {test_user.username}")
        else:
            print("No users found to create a test goal!")
    
    print("\n==== DIAGNOSTICS COMPLETE ====")
