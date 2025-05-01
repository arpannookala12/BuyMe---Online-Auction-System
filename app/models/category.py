from app import db
from datetime import datetime

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('Item', backref='category', lazy=True)
    alerts = db.relationship('Alert', backref='category', lazy=True)
    subcategories = db.relationship('Category',
                                  backref=db.backref('parent', remote_side=[id]),
                                  lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def get_all_subcategories(self):
        """Get all subcategories recursively"""
        all_subcats = []
        for subcat in self.subcategories:
            all_subcats.append(subcat)
            all_subcats.extend(subcat.get_all_subcategories())
        return all_subcats
    
    def get_breadcrumbs(self):
        """Get category breadcrumbs from root to this category"""
        breadcrumbs = []
        current = self
        while current:
            breadcrumbs.insert(0, current)
            current = current.parent
        return breadcrumbs

class CategoryAttribute(db.Model):
    __tablename__ = 'category_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    attribute_type = db.Column(db.String(50), nullable=False)  # text, number, boolean, select
    required = db.Column(db.Boolean, default=False)
    options = db.Column(db.Text)  # JSON string for select type attributes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CategoryAttribute {self.name} for {self.category.name}>'
    
    @property
    def options_list(self):
        """Get the options as a list for select type attributes"""
        if self.attribute_type == 'select' and self.options:
            return [opt.strip() for opt in self.options.split(',')]
        return []
