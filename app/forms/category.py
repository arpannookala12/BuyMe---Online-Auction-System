from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Optional

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    parent_id = SelectField('Parent Category', coerce=int, validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        from app.models import Category
        self.parent_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Category.query.order_by('name')]

class CategoryAttributeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    display_name = StringField('Display Name', validators=[DataRequired()])
    attribute_type = SelectField('Type', choices=[
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Yes/No'),
        ('select', 'Select from List')
    ], validators=[DataRequired()])
    required = BooleanField('Required')
    options = TextAreaField('Options (comma-separated for select type)', validators=[Optional()]) 