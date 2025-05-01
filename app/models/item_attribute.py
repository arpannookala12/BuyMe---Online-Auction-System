from app import db
class ItemAttributeValue(db.Model):
    __tablename__ = 'item_attribute_values'
    id                     = db.Column(db.Integer, primary_key=True)
    item_id                = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    attribute_definition_id= db.Column(db.Integer, db.ForeignKey('attribute_definitions.id'), nullable=False)
    value_string           = db.Column(db.String(255))
    value_integer          = db.Column(db.Integer)
    value_decimal          = db.Column(db.Numeric(10,2))
    value_date             = db.Column(db.Date)

    item                   = db.relationship('Item', backref='attribute_values')
    definition             = db.relationship('AttributeDefinition')