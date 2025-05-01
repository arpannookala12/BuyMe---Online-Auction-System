from datetime import datetime
from app import db

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    auction = db.relationship('Auction', back_populates='auction_reviews', lazy=True)
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviews_given', lazy=True)
    seller = db.relationship('User', foreign_keys=[seller_id], back_populates='reviews_received', lazy=True)
    
    def __init__(self, auction_id, reviewer_id, seller_id, rating, comment=None):
        self.auction_id = auction_id
        self.reviewer_id = reviewer_id
        self.seller_id = seller_id
        self.rating = rating
        self.comment = comment
    
    def __repr__(self):
        return f'<Review {self.id}>'
    
    @staticmethod
    def get_seller_rating(seller_id):
        """Calculate average rating for a seller"""
        reviews = Review.query.filter_by(seller_id=seller_id).all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)
    
    @staticmethod
    def get_seller_reviews(seller_id):
        """Get all reviews for a seller"""
        return Review.query.filter_by(seller_id=seller_id).order_by(Review.created_at.desc()).all()