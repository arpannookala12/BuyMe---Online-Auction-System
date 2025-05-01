from app import db

class CategoryAttribute(db.Model):
    __tablename__ = 'category_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    display_name = db.Column(db.String(64), nullable=False)
    attribute_type = db.Column(db.String(32), nullable=False)  # text, number, select, etc.
    required = db.Column(db.Boolean, default=False)
    options = db.Column(db.Text)  # Comma-separated list of options for select type
    
    # Relationship
    category = db.relationship('Category', backref=db.backref('attributes', lazy='dynamic'))
    
    def __repr__(self):
        return f'<CategoryAttribute {self.name} for Category {self.category_id}>'