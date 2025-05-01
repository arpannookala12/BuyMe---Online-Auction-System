from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_customer_rep = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    auctions_sold = db.relationship('Auction', foreign_keys='Auction.seller_id', back_populates='seller', lazy=True)
    auctions_won = db.relationship('Auction', foreign_keys='Auction.winner_id', back_populates='winner', lazy=True)
    bids = db.relationship('Bid', back_populates='bidder', lazy=True)
    alerts = db.relationship('Alert', back_populates='user', lazy=True)
    notifications = db.relationship('Notification', back_populates='user', lazy=True)
    questions = db.relationship('Question', back_populates='user', lazy=True)
    answers = db.relationship('Answer', back_populates='user', lazy=True)
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', back_populates='reviewer', lazy=True)
    reviews_received = db.relationship('Review', foreign_keys='Review.seller_id', back_populates='seller', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_active_alerts(self):
        """Get all active alerts for the user."""
        return [alert for alert in self.alerts if alert.is_active]
    
    def get_unread_notifications(self):
        """Get all unread notifications for the user."""
        return [notif for notif in self.notifications if not notif.is_read]
    
    def get_auction_history(self):
        """Get all auctions where the user has placed bids."""
        return list(set(bid.auction for bid in self.bids))
    
    def get_won_auctions(self):
        """Get all auctions won by the user."""
        return self.auctions_won
    
    def get_active_bids(self):
        """Get all active bids (on non-ended auctions)."""
        return [bid for bid in self.bids if not bid.auction.is_ended]
    
    def get_seller_rating(self):
        """Calculate the seller's average rating."""
        reviews = self.reviews_received
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

