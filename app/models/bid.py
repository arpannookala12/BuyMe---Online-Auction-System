from app import db
from datetime import datetime

class Bid(db.Model):
    __tablename__ = 'bids'
    
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id'), nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    is_auto_bid = db.Column(db.Boolean, default=False)
    auto_bid_limit = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    auction = db.relationship('Auction', back_populates='bids', lazy=True)
    bidder = db.relationship('User', back_populates='bids', lazy=True)
    
    def __init__(self, auction_id, bidder_id, amount, is_auto_bid=False, auto_bid_limit=None):
        self.auction_id = auction_id
        self.bidder_id = bidder_id
        self.amount = amount
        self.is_auto_bid = is_auto_bid
        self.auto_bid_limit = auto_bid_limit
    
    def __repr__(self):
        return f'<Bid {self.id}>' 