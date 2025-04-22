from datetime import datetime
from app import db

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Alert criteria
    keywords = db.Column(db.String(256), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    min_price = db.Column(db.Float, nullable=True)
    max_price = db.Column(db.Float, nullable=True)
    
    # Alert settings
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Category')
    
    def __repr__(self):
        return f'<Alert {self.id} for User {self.user_id}>'
    
    def matches_item(self, item, auction):
        """Check if an item matches the alert criteria"""
        # Category check
        if self.category_id and item.category_id != self.category_id:
            parent_cat = item.category.parent_id
            # Check parent categories too
            while parent_cat:
                if parent_cat == self.category_id:
                    break
                parent_cat_obj = Category.query.get(parent_cat)
                if not parent_cat_obj:
                    break
                parent_cat = parent_cat_obj.parent_id
            else:
                return False
        
        # Keyword check
        if self.keywords:
            keywords = [k.strip().lower() for k in self.keywords.split(',')]
            item_text = (item.name + ' ' + (item.description or '')).lower()
            if not any(k in item_text for k in keywords):
                return False
        
        # Price check
        if self.min_price is not None and auction.initial_price < self.min_price:
            return False
        if self.max_price is not None and auction.initial_price > self.max_price:
            return False
            
        return True


# Import at the bottom to avoid circular imports
from app.models.item import Category