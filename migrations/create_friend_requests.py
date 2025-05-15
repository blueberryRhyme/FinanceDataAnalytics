import os
import sys

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

from flask import Flask
from app import create_app, db
from app.models import FriendRequest

def run_migration():
    """Create the friend_requests table in the database"""
    print("Starting migration to create friend_requests table...")
    app = create_app()
    
    with app.app_context():
        print("Creating friend_requests table...")
        db.create_all()
        print("Friend requests table created successfully!")

if __name__ == "__main__":
    run_migration()
