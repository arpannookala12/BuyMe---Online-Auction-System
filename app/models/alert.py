from datetime import datetime
from app import db
import logging
from app.models.item import Category  # Moved import to the top

logger = logging.getLogger(__name__)

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    keywords = db.Column(db.String(255))
    min_price = db.Column(db.Float)
    max_price = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='alerts', lazy=True)
    
    def __repr__(self):
        return f'<Alert {self.id}>'
    
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

    def matches_auction(self, auction):
        """Check if an auction matches the alert criteria"""
        logger.debug(f"Checking alert {self.id} against auction {auction.id}")
        
        # Category check
        if self.category_id:
            logger.debug(f"Checking category match: alert category {self.category_id} vs auction category {auction.item.category_id}")
            if auction.item.category_id != self.category_id:
                # Get all parent categories
                parent_categories = set()
                current_cat = auction.item.category
                while current_cat and current_cat.parent_id:
                    parent_categories.add(current_cat.parent_id)
                    current_cat = Category.query.get(current_cat.parent_id)
                
                if self.category_id not in parent_categories:
                    logger.debug("Category mismatch")
                    return False
        
        # Keyword check
        if self.keywords:
            logger.debug(f"Checking keywords: {self.keywords}")
            keywords = [k.strip().lower() for k in self.keywords.split(',')]
            
            # Combine all searchable text
            search_text = [
                auction.title.lower(),
                auction.description.lower() if auction.description else '',
                auction.item.name.lower(),
                auction.item.description.lower() if auction.item.description else ''
            ]
            
            # Add attributes to search text
            if hasattr(auction.item, 'attributes'):
                try:
                    attributes = auction.item.attributes
                    if isinstance(attributes, dict):
                        search_text.extend(str(v).lower() for v in attributes.values())
                except Exception as e:
                    logger.warning(f"Error processing item attributes: {str(e)}")
            
            search_text = ' '.join(filter(None, search_text))
            
            if not any(k in search_text for k in keywords):
                logger.debug("No keyword matches found")
                return False
        
        # Price check
        if self.min_price is not None and auction.initial_price < self.min_price:
            logger.debug(f"Price below minimum: {auction.initial_price} < {self.min_price}")
            return False
        if self.max_price is not None and auction.initial_price > self.max_price:
            logger.debug(f"Price above maximum: {auction.initial_price} > {self.max_price}")
            return False
        
        logger.debug("Alert matches auction")
        return True