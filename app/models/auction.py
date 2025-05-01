from datetime import datetime
from app import db
from sqlalchemy import event
from app.models.item import Item

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
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    winner_notified = db.Column(db.Boolean, default=False)
    
    # Relationships
    item = db.relationship('Item', back_populates='auctions')
    seller = db.relationship('User', foreign_keys=[seller_id], back_populates='auctions_sold')
    winner = db.relationship('User', foreign_keys=[winner_id], back_populates='auctions_won')
    bids = db.relationship('Bid', back_populates='auction', lazy=True)
    questions = db.relationship('Question', back_populates='auction')
    auction_reviews = db.relationship('Review', back_populates='auction')
    
    def __repr__(self):
        return f'<Auction {self.title}>'
    
    @property
    def current_price(self):
        """Return the current highest bid amount or the initial price if no bids"""
        if not self.bids:
            return self.initial_price
        return max(bid.amount for bid in self.bids) if self.bids else self.initial_price
    
    @property
    def highest_bidder(self):
        """Return the user with the highest bid"""
        if not self.bids:
            return None
        highest_bid = max(self.bids, key=lambda bid: bid.amount)
        return highest_bid.bidder
    
    @property
    def num_bids(self):
        """Return the number of bids"""
        return len(self.bids) if self.bids else 0
    
    @property
    def is_reserve_met(self):
        """Check if the reserve price is met"""
        return self.current_price >= self.secret_min_price
    
    @property
    def is_ended(self):
        """Check if the auction has ended"""
        now = datetime.utcnow()
        if now >= self.end_time:
            if self.is_active:
                self.is_active = False
                db.session.commit()
            return True
        return False
    
    def next_valid_bid_amount(self):
        """Calculate the minimum valid bid amount"""
        return self.current_price + self.min_increment
    
    def determine_winner(self):
        """Determine the winner of the auction"""
        if not self.is_ended:
            return None
            
        if not self.bids:
            self.is_active = False
            db.session.commit()
            return None
            
        highest_bid = max(self.bids, key=lambda bid: bid.amount)
        if highest_bid.amount >= self.secret_min_price:
            self.winner_id = highest_bid.bidder_id
            self.is_active = False
            db.session.commit()
            return self.winner
        return None
    
    def check_status(self):
        """Check and update auction status"""
        if self.is_ended and self.is_active:
            self.is_active = False
            winner = self.determine_winner()
            db.session.commit()
            return winner
        return None
    
    def get_bid_history(self):
        """Get complete bid history with bidder information"""
        return sorted(self.bids, key=lambda bid: bid.created_at, reverse=True) if self.bids else []
    
    def get_similar_auctions(self, limit=4):
        """Get similar active auctions in the same category"""
        if not self.item or not self.item.category_id:
            return []
            
        return Auction.query.join(Item).filter(
            Item.category_id == self.item.category_id,
            Auction.id != self.id,
            Auction.is_active == True,
            Auction.end_time > datetime.utcnow()
        ).limit(limit).all()

# Add event listener to automatically check status when loading auction
@event.listens_for(Auction, 'load')
def check_auction_status(target, context):
    """Check auction status when loading from database"""
    if target.is_active and datetime.utcnow() >= target.end_time:
        target.is_active = False
        target.determine_winner()
        db.session.commit()