from datetime import datetime
from app import db

class Auction(db.Model):
    __tablename__ = 'auctions'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    
    # Auction settings
    initial_price = db.Column(db.Float, nullable=False)
    min_increment = db.Column(db.Float, nullable=False)
    secret_min_price = db.Column(db.Float, nullable=False)  # Reserve price
    
    # Timestamps
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    bids = db.relationship('Bid', backref='auction', lazy='dynamic')
    
    def __repr__(self):
        return f'<Auction {self.title}>'
    
    @property
    def current_price(self):
        """Return the current highest bid amount or the initial price if no bids"""
        highest_bid = self.bids.order_by(Bid.amount.desc()).first()
        return highest_bid.amount if highest_bid else self.initial_price
    
    @property
    def highest_bidder(self):
        """Return the user with the highest bid"""
        highest_bid = self.bids.order_by(Bid.amount.desc()).first()
        return highest_bid.bidder if highest_bid else None
    
    @property
    def num_bids(self):
        """Return the number of bids"""
        return self.bids.count()
    
    @property
    def is_reserve_met(self):
        """Check if the reserve price is met"""
        return self.current_price >= self.secret_min_price
    
    @property
    def is_ended(self):
        """Check if the auction has ended"""
        return datetime.utcnow() > self.end_time
    
    def next_valid_bid_amount(self):
        """Calculate the minimum valid bid amount"""
        return self.current_price + self.min_increment


class Bid(db.Model):
    __tablename__ = 'bids'
    
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id'), nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    auto_bid_limit = db.Column(db.Float, nullable=True)  # For auto-bidding
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Bid ${self.amount} on Auction {self.auction_id}>'