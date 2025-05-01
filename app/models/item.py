from datetime import datetime
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SelectField, DateField
from wtforms.validators import InputRequired
import json

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
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    attributes = db.Column(db.Text)  # JSON string storing attribute values
    image_url = db.Column(db.String(255))  # URL to the item's image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    auctions = db.relationship('Auction', back_populates='item', lazy=True)
    
    def __repr__(self):
        return f'<Item {self.name}>'
    
    @property
    def attribute_values(self):
        """Get the attribute values as a dictionary"""
        if self.attributes:
            return json.loads(self.attributes)
        return {}
    
    @attribute_values.setter
    def attribute_values(self, values):
        """Set the attribute values from a dictionary"""
        self.attributes = json.dumps(values)
    
    def get_attribute_value(self, name, default=None):
        """Get a specific attribute value"""
        return self.attribute_values.get(name, default)
    
    def set_attribute_value(self, name, value):
        """Set a specific attribute value"""
        values = self.attribute_values
        values[name] = value
        self.attribute_values = values
    
    def validate_attributes(self):
        """Validate that all required attributes are present and have valid values"""
        if not self.category:
            return False, "Item must belong to a category"
        
        for attr in self.category.attributes:
            if attr.required and attr.name not in self.attribute_values:
                return False, f"Required attribute '{attr.display_name}' is missing"
            
            if attr.name in self.attribute_values:
                value = self.attribute_values[attr.name]
                
                if attr.attribute_type == 'number':
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        return False, f"Attribute '{attr.display_name}' must be a number"
                
                elif attr.attribute_type == 'select':
                    if value not in attr.options_list:
                        return False, f"Invalid value for attribute '{attr.display_name}'"
        
        return True, None