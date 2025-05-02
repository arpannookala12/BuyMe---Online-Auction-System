from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Item, Category, AttributeDefinition
from app.models.user import User
from datetime import datetime
import json

item_bp = Blueprint('item', __name__, url_prefix='/item')

@item_bp.route('/<int:id>')
def view(id):
    """View details of a specific item"""
    item = Item.query.get_or_404(id)
    return render_template('item/view.html', item=item, now=datetime.utcnow)

@item_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new item (independently of an auction)"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description')
        category_id = request.form.get('category_id', type=int)
        
        # Validate input
        if not all([name, description, category_id]):
            flash('All fields are required', 'danger')
            categories = Category.query.all()
            return render_template('item/create.html', categories=categories)
        
        # Create item
        item = Item(
            name=name,
            description=description,
            category_id=category_id
        )
        
        # Process custom attributes
        attributes = {}
        for key, value in request.form.items():
            if key.startswith('attribute_') and value:
                attr_name = key[10:]  # Remove 'attribute_' prefix
                attributes[attr_name] = value
        
        item.set_attributes(attributes)
        
        db.session.add(item)
        db.session.commit()
        
        flash('Item created successfully!', 'success')
        return redirect(url_for('item.view', id=item.id))
    
    # GET request - show the create form
    categories = Category.query.all()
    return render_template('item/create.html', categories=categories)

@item_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit an existing item"""
    item = Item.query.get_or_404(id)
    
    # Check if user is authorized to edit this item
    # (owns it or is admin/customer rep)
    auctions = item.auctions.all()
    is_owner = any(auction.seller_id == current_user.id for auction in auctions)
    if not (is_owner or current_user.is_admin() or current_user.is_customer_rep()):
        flash('You are not authorized to edit this item', 'danger')
        return redirect(url_for('item.view', id=id))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description')
        category_id = request.form.get('category_id', type=int)
        
        # Validate input
        if not all([name, description, category_id]):
            flash('All fields are required', 'danger')
            categories = Category.query.all()
            return render_template('item/edit.html', item=item, categories=categories)
        
        # Update item
        item.name = name
        item.description = description
        item.category_id = category_id
        
        # Process custom attributes
        attributes = {}
        for key, value in request.form.items():
            if key.startswith('attribute_') and value:
                attr_name = key[10:]  # Remove 'attribute_' prefix
                attributes[attr_name] = value
        
        item.set_attributes(attributes)
        
        db.session.commit()
        
        flash('Item updated successfully!', 'success')
        return redirect(url_for('item.view', id=id))
    
    # GET request - show the edit form
    categories = Category.query.all()
    return render_template('item/edit.html', item=item, categories=categories)

@item_bp.route('/types', methods=['GET'])
@login_required
def manage_types():
    """View and manage item types (categories) and their attributes."""
    if not current_user.is_admin:
        flash('You do not have permission to manage item types.', 'danger')
        return redirect(url_for('main.index'))
    
    categories = Category.query.all()
    return render_template('item/manage_types.html', categories=categories)

@item_bp.route('/type/create', methods=['GET', 'POST'])
@login_required
def create_type():
    """Create a new item type (category)."""
    if not current_user.is_admin:
        flash('You do not have permission to create item types.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        parent_id = request.form.get('parent_id', type=int)
        
        if not name:
            flash('Name is required', 'error')
            return redirect(url_for('item.create_type'))
        
        category = Category(
            name=name,
            description=description,
            parent_id=parent_id
        )
        db.session.add(category)
        db.session.commit()
        
        flash('Item type created successfully!', 'success')
        return redirect(url_for('item.manage_types'))
    
    categories = Category.query.all()
    return render_template('item/create_type.html', categories=categories)

@item_bp.route('/type/<int:id>/attributes', methods=['GET', 'POST'])
@login_required
def manage_attributes(id):
    """Manage attributes for an item type."""
    if not current_user.is_admin:
        flash('You do not have permission to manage attributes.', 'danger')
        return redirect(url_for('main.index'))
    
    category = Category.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        data_type = request.form.get('data_type')
        required = request.form.get('required') == 'true'
        enum_values = request.form.get('enum_values')
        
        if not name or not data_type:
            flash('Name and data type are required', 'error')
            return redirect(url_for('item.manage_attributes', id=id))
        
        if data_type == 'enum' and not enum_values:
            flash('Enum values are required for enum type', 'error')
            return redirect(url_for('item.manage_attributes', id=id))
        
        attribute = AttributeDefinition(
            category_id=id,
            name=name,
            data_type=data_type,
            required=required,
            enum_values=enum_values
        )
        db.session.add(attribute)
        db.session.commit()
        
        flash('Attribute added successfully!', 'success')
        return redirect(url_for('item.manage_attributes', id=id))
    
    return render_template('item/manage_attributes.html', category=category)

@item_bp.route('/type/<int:id>/delete', methods=['POST'])
@login_required
def delete_type(id):
    """Delete an item type."""
    if not current_user.is_admin:
        flash('You do not have permission to delete item types.', 'danger')
        return redirect(url_for('main.index'))
    
    category = Category.query.get_or_404(id)
    
    # Check if category has items
    if category.items.count() > 0:
        flash('Cannot delete category with existing items', 'error')
        return redirect(url_for('item.manage_types'))
    
    # Delete attributes first
    AttributeDefinition.query.filter_by(category_id=id).delete()
    
    # Delete category
    db.session.delete(category)
    db.session.commit()
    
    flash('Item type deleted successfully!', 'success')
    return redirect(url_for('item.manage_types'))

@item_bp.route('/attribute/<int:id>/delete', methods=['POST'])
@login_required
def delete_attribute(id):
    """Delete an attribute from an item type."""
    if not current_user.is_admin:
        flash('You do not have permission to delete attributes.', 'danger')
        return redirect(url_for('main.index'))
    
    attribute = AttributeDefinition.query.get_or_404(id)
    category_id = attribute.category_id
    
    # Check if attribute is used in any items
    items = Item.query.filter_by(category_id=category_id).all()
    for item in items:
        if attribute.name in item.attribute_values:
            flash('Cannot delete attribute that is used in items', 'error')
            return redirect(url_for('item.manage_attributes', id=category_id))
    
    db.session.delete(attribute)
    db.session.commit()
    
    flash('Attribute deleted successfully!', 'success')
    return redirect(url_for('item.manage_attributes', id=category_id))