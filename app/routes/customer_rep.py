from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Auction, Bid
from functools import wraps

customer_rep_bp = Blueprint('customer_rep', __name__, url_prefix='/rep')

# Custom decorator to check if the user is a customer representative
def customer_rep_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_customer_rep():
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@customer_rep_bp.route('/dashboard')
@login_required
@customer_rep_required
def dashboard():
    # Get basic statistics
    user_count = User.query.filter_by(role='user').count()
    active_auctions = Auction.query.filter_by(is_active=True).count()
    total_bids = Bid.query.count()
    
    # Get recent auctions
    recent_auctions = Auction.query.order_by(Auction.created_at.desc()).limit(10).all()
    
    return render_template('customer_rep/dashboard.html', 
                          user_count=user_count,
                          active_auctions=active_auctions,
                          total_bids=total_bids,
                          recent_auctions=recent_auctions)

@customer_rep_bp.route('/users')
@login_required
@customer_rep_required
def manage_users():
    # Get search parameter
    search = request.args.get('search', '')
    
    # Query users
    if search:
        users = User.query.filter(
            (User.username.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        ).order_by(User.created_at.desc()).all()
    else:
        users = User.query.order_by(User.created_at.desc()).all()
    
    return render_template('customer_rep/users.html', users=users, search=search)

@customer_rep_bp.route('/users/<int:id>')
@login_required
@customer_rep_required
def view_user(id):
    user = User.query.get_or_404(id)
    
    # Get user's auctions
    auctions = Auction.query.filter_by(seller_id=id).order_by(Auction.created_at.desc()).all()
    
    # Get user's bids
    bids = Bid.query.filter_by(bidder_id=id).order_by(Bid.created_at.desc()).all()
    
    return render_template('customer_rep/view_user.html', user=user, auctions=auctions, bids=bids)

@customer_rep_bp.route('/users/<int:id>/reset-password', methods=['POST'])
@login_required
@customer_rep_required
def reset_password(id):
    user = User.query.get_or_404(id)
    
    # Generate a temporary password (in a real app, you might want to send this via email)
    temp_password = 'TemporaryPass123'
    user.set_password(temp_password)
    db.session.commit()
    
    flash(f'Password reset for {user.username}. Temporary password: {temp_password}', 'success')
    return redirect(url_for('customer_rep.view_user', id=id))

@customer_rep_bp.route('/auctions')
@login_required
@customer_rep_required
def manage_auctions():
    # Get search parameter
    search = request.args.get('search', '')
    
    # Query auctions
    if search:
        auctions = Auction.query.filter(
            (Auction.title.ilike(f'%{search}%')) |
            (Auction.description.ilike(f'%{search}%'))
        ).order_by(Auction.created_at.desc()).all()
    else:
        auctions = Auction.query.order_by(Auction.created_at.desc()).all()
    
    return render_template('customer_rep/auctions.html', auctions=auctions, search=search)

@customer_rep_bp.route('/auctions/<int:id>/remove-bid/<int:bid_id>', methods=['POST'])
@login_required
@customer_rep_required
def remove_bid(id, bid_id):
    auction = Auction.query.get_or_404(id)
    bid = Bid.query.get_or_404(bid_id)
    
    # Check if the bid belongs to the auction
    if bid.auction_id != id:
        flash('Bid does not belong to this auction', 'danger')
        return redirect(url_for('auction.view', id=id))
    
    # Remove the bid
    db.session.delete(bid)
    db.session.commit()
    
    flash('Bid removed successfully', 'success')
    return redirect(url_for('auction.view', id=id))

@customer_rep_bp.route('/auctions/<int:id>/toggle', methods=['POST'])
@login_required
@customer_rep_required
def toggle_auction(id):
    auction = Auction.query.get_or_404(id)
    
    # Toggle the active status
    auction.is_active = not auction.is_active
    db.session.commit()
    
    status = 'activated' if auction.is_active else 'deactivated'
    flash(f'Auction {status} successfully', 'success')
    return redirect(url_for('auction.view', id=id))