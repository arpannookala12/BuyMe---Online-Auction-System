from app import db
class AttributeDefinition(db.Model):
    __tablename__ = 'attribute_definitions'
    id           = db.Column(db.Integer, primary_key=True)
    category_id  = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name         = db.Column(db.String(50), nullable=False)
    data_type    = db.Column(db.Enum('string','integer','decimal','date','enum'), nullable=False)
    required     = db.Column(db.Boolean, default=False)
    enum_values  = db.Column(db.Text)  
    # e.g. comma-separated values for enum types

    category     = db.relationship('Category', backref='attributes')