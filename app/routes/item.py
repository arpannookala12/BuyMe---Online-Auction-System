from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Item, Category

item_bp = Blueprint('item', __name__, url_prefix='/item')

@item_bp.route('/<int:id>')
def view(id):
    """View details of a specific item"""
    item = Item.query.get_or_404(id)
    return render_template('item/view.html', item=item)

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