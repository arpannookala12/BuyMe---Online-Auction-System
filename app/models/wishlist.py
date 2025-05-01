from datetime import datetime
from app import db

class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)  # Optional notes/comments about why user wants this item
    
    # Relationships
    user = db.relationship('User', backref=db.backref('wishlist_items', lazy=True))
    item = db.relationship('Item', backref=db.backref('wishlist_entries', lazy=True))
    
    def __repr__(self):
        return f'<Wishlist {self.id} - User {self.user_id}, Item {self.item_id}>'