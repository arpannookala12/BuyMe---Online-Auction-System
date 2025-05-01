from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange
from app.models import Category

class ItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
        
        # Add dynamic fields based on category attributes
        if 'category_id' in kwargs:
            category = Category.query.get(kwargs['category_id'])
            if category:
                for attr in category.attributes:
                    if attr.attribute_type == 'text':
                        field = StringField(attr.display_name, validators=[DataRequired() if attr.required else Optional()])
                    elif attr.attribute_type == 'number':
                        field = DecimalField(attr.display_name, validators=[DataRequired() if attr.required else Optional()])
                    elif attr.attribute_type == 'boolean':
                        field = BooleanField(attr.display_name)
                    elif attr.attribute_type == 'select':
                        field = SelectField(attr.display_name, 
                                          choices=[(opt, opt) for opt in attr.options_list],
                                          validators=[DataRequired() if attr.required else Optional()])
                    
                    setattr(self, f'attr_{attr.name}', field)
    
    def get_attribute_values(self):
        """Get all attribute values from the form"""
        values = {}
        for field_name, field in self._fields.items():
            if field_name.startswith('attr_'):
                attr_name = field_name[5:]  # Remove 'attr_' prefix
                values[attr_name] = field.data
        return values 