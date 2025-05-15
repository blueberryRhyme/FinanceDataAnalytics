"""
Achievement hooks for FinShare
This module contains event hooks that trigger achievement checks
when certain actions occur in the application.
"""

from flask import current_app
from app.achievement_engine import check_achievements

def register_achievement_hooks(app):
    """Register achievement event hooks with the Flask application"""
    
    # Import models here to avoid circular imports
    from app.models import Transaction, Bill, User
    from sqlalchemy import event
    
    @event.listens_for(Transaction, 'after_insert')
    def transaction_created(mapper, connection, target):
        """Trigger achievement checks when a transaction is created"""
        # Use Flask's app context
        with app.app_context():
            # Pass the transaction as context
            check_achievements(target.user_id, context={'transaction': target})
    
    @event.listens_for(Bill, 'after_insert')
    def bill_created(mapper, connection, target):
        """Trigger achievement checks when a bill is created"""
        with app.app_context():
            check_achievements(target.created_by, context={'bill': target})
    
    @app.before_request
    def check_streak_achievements():
        """Check streak-based achievements on page load"""
        # This would be too resource-intensive to check on every request
        # In a real app, we'd move this to a daily scheduled task
        pass
    
    # Add a listener for when friends are added
    @event.listens_for(User.friends, 'append')
    def friend_added(target, value, initiator):
        """Trigger achievement checks when a friend is added"""
        with app.app_context():
            check_achievements(target.id, context={'new_friend': value})
    
    # Add hooks for budget updates
    @app.context_processor
    def check_monthly_budget():
        """
        Add a utility function to templates to check budget-related achievements
        This would be called from relevant templates that show budget info
        """
        def check_budget_achievements(user_id):
            with app.app_context():
                return check_achievements(user_id, context={'budget_check': True})
        return dict(check_budget_achievements=check_budget_achievements)
    
    # Log that hooks have been registered
    app.logger.info("Achievement hooks registered successfully.")
