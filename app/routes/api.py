from flask import Blueprint, jsonify
from app.models import Category, CategoryAttribute

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/category/<int:category_id>/attributes')
def get_category_attributes(category_id):
    """Get all attributes for a category"""
    attributes = CategoryAttribute.query.filter_by(category_id=category_id).all()
    
    result = {
        'attributes': [
            {
                'id': attr.id,
                'name': attr.name,
                'display_name': attr.display_name,
                'attribute_type': attr.attribute_type,
                'required': attr.required,
                'options': attr.options
            }
            for attr in attributes
        ]
    }
    
    return jsonify(result)