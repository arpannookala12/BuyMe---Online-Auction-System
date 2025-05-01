from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Wishlist, Item, Auction

wishlist_bp = Blueprint('wishlist', __name__, url_prefix='/wishlist')

@wishlist_bp.route('/')
@login_required
def view():
    """View user's wishlist"""
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    
    # Get active auctions for wishlist items
    items_with_auctions = []
    for entry in wishlist_items:
        # Find active auctions for this item
        active_auctions = Auction.query.filter_by(
            item_id=entry.item_id, 
            is_active=True
        ).all()
        
        items_with_auctions.append({
            'wishlist_entry': entry,
            'item': entry.item,
            'active_auctions': active_auctions
        })
    
    return render_template('wishlist/view.html', items_with_auctions=items_with_auctions)

@wishlist_bp.route('/add/<int:item_id>', methods=['POST'])
@login_required
def add(item_id):
    """Add an item to wishlist"""
    # Check if item exists
    item = Item.query.get_or_404(item_id)
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        item_id=item_id
    ).first()
    
    if existing:
        flash(f'{item.name} is already in your wishlist', 'info')
        return redirect(url_for('wishlist.view'))
    
    # Get optional notes
    notes = request.form.get('notes', '')
    
    # Add to wishlist
    wishlist_entry = Wishlist(
        user_id=current_user.id,
        item_id=item_id,
        notes=notes
    )
    
    db.session.add(wishlist_entry)
    db.session.commit()
    
    flash(f'{item.name} added to your wishlist', 'success')
    
    # If this is an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success'})
    
    # Otherwise redirect
    return redirect(url_for('wishlist.view'))

@wishlist_bp.route('/remove/<int:wishlist_id>', methods=['POST'])
@login_required
def remove(wishlist_id):
    """Remove an item from wishlist"""
    wishlist_entry = Wishlist.query.get_or_404(wishlist_id)
    
    # Check if the wishlist entry belongs to the current user
    if wishlist_entry.user_id != current_user.id:
        flash('You cannot remove this item from wishlist', 'danger')
        return redirect(url_for('wishlist.view'))
    
    item_name = wishlist_entry.item.name
    
    db.session.delete(wishlist_entry)
    db.session.commit()
    
    flash(f'{item_name} removed from your wishlist', 'success')
    
    # If this is an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success'})
    
    # Otherwise redirect
    return redirect(url_for('wishlist.view'))

@wishlist_bp.route('/toggle/<int:item_id>', methods=['POST'])
@login_required
def toggle(item_id):
    """Toggle an item in the wishlist (add if not exists, remove if exists)"""
    # Check if item exists
    item = Item.query.get_or_404(item_id)
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        item_id=item_id
    ).first()
    
    result = {}
    
    if existing:
        # Remove from wishlist
        db.session.delete(existing)
        db.session.commit()
        result = {
            'status': 'success',
            'action': 'removed',
            'message': f'{item.name} removed from your wishlist'
        }
        flash(result['message'], 'success')
    else:
        # Add to wishlist
        notes = request.form.get('notes', '')
        wishlist_entry = Wishlist(
            user_id=current_user.id,
            item_id=item_id,
            notes=notes
        )
        db.session.add(wishlist_entry)
        db.session.commit()
        result = {
            'status': 'success',
            'action': 'added',
            'message': f'{item.name} added to your wishlist'
        }
        flash(result['message'], 'success')
    
    # If this is an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(result)
    
    # Otherwise redirect back to the previous page
    return redirect(request.referrer or url_for('wishlist.view'))