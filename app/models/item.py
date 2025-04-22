from datetime import datetime
from app import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    # Self-referential relationship for hierarchical categories
    subcategories = db.relationship('Category', 
                                   backref=db.backref('parent', remote_side=[id]),
                                   lazy='dynamic')
    items = db.relationship('Item', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    image_url = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Custom attributes (will be stored as JSON in a real implementation)
    # For simplicity, we'll use a text field with comma-separated values
    attributes = db.Column(db.Text)  
    
    # Relationship
    auctions = db.relationship('Auction', backref='item', lazy='dynamic')
    
    def __repr__(self):
        return f'<Item {self.name}>'
    
    def get_attributes(self):
        """Convert the attributes string to a dictionary"""
        if not self.attributes:
            return {}
        
        result = {}
        pairs = self.attributes.split(',')
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                result[key.strip()] = value.strip()
        
        return result
    
    def set_attributes(self, attr_dict):
        """Convert the dictionary to a string for storage"""
        if not attr_dict:
            self.attributes = None
            return
        
        pairs = [f"{key}:{value}" for key, value in attr_dict.items()]
        self.attributes = ','.join(pairs)