from app import db
from datetime import datetime

class Notification(db.Model):
    """Model for user notifications."""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., 'bid_placed', 'auction_ended', 'outbid', 'new_question', 'question_answered', 'new_auction'
    message = db.Column(db.String(255), nullable=False)
    reference_id = db.Column(db.Integer)  # ID of related entity (e.g., auction_id, question_id)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='notifications', lazy=True)
    
    def __init__(self, user_id, type, message, reference_id=None):
        self.user_id = user_id
        self.type = type
        self.message = message
        self.reference_id = reference_id
        self.is_read = False
    
    def mark_as_read(self):
        """Mark the notification as read."""
        self.is_read = True
    
    @classmethod
    def mark_all_read(cls, user_id):
        """Mark all notifications as read for a user."""
        cls.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    
    @classmethod
    def get_unread_count(cls, user_id):
        """Get the count of unread notifications for a user."""
        return cls.query.filter_by(user_id=user_id, is_read=False).count()
    
    @classmethod
    def create_bid_notification(cls, user_id, auction_id, bid_amount):
        """Create a notification for a new bid."""
        message = f"New bid of ${bid_amount:.2f} placed on your auction"
        return cls(user_id=user_id, type='bid_placed', message=message, reference_id=auction_id)
    
    @classmethod
    def create_outbid_notification(cls, user_id, auction_id, bid_amount):
        """Create a notification for being outbid."""
        message = f"You have been outbid. Current highest bid is ${bid_amount:.2f}"
        return cls(user_id=user_id, type='outbid', message=message, reference_id=auction_id)
    
    @classmethod
    def create_auction_ended_notification(cls, user_id, auction_id, is_winner=False):
        """Create a notification for auction end."""
        if is_winner:
            message = "Congratulations! You won the auction"
        else:
            message = "The auction has ended"
        return cls(user_id=user_id, type='auction_ended', message=message, reference_id=auction_id)
    
    @classmethod
    def create_auction_created_notification(cls, user_id, auction_id):
        """Create a notification for new auction creation."""
        message = "A new auction matching your alert has been created"
        return cls(user_id=user_id, type='auction_created', message=message, reference_id=auction_id)
    
    @classmethod
    def create_question_notification(cls, question_id, auction_id, user_id):
        """Create a notification for a new question."""
        message = f"New question posted on auction {auction_id}"
        return cls(user_id=user_id, type='new_question', message=message, reference_id=question_id)
    
    @classmethod
    def create_answer_notification(cls, answer_id, question_id, user_id):
        """Create a notification for a new answer."""
        message = f"Your question has been answered"
        return cls(user_id=user_id, type='question_answered', message=message, reference_id=answer_id)
    
    @classmethod
    def create_new_auction_notification(cls, auction_id, user_id):
        """Create a notification for a new auction."""
        message = f"New auction posted in your category"
        return cls(user_id=user_id, type='new_auction', message=message, reference_id=auction_id)
    
    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'reference_id': self.reference_id
        } 