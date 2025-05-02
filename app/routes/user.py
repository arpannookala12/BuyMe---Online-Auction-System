from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Auction, Bid, Review, Question, Answer
from datetime import datetime, timezone

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html', user=current_user)

@user_bp.route('/update', methods=['POST'])
@login_required
def update_profile():
    # Get form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    address = request.form.get('address')
    phone = request.form.get('phone')
    
    # Update user
    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.address = address
    current_user.phone = phone
    
    # Check if password is being updated
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if current_password and new_password and confirm_password:
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('user.profile'))
        
        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('user.profile'))
        
        # Update password
        current_user.set_password(new_password)
        flash('Password updated successfully', 'success')
    
    # Save changes
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('user.profile'))

@user_bp.route('/my-auctions')
@login_required
def my_auctions():
    # Get auction status filter
    status = request.args.get('status', 'active')
    
    # Get current time for comparison
    current_time = datetime.utcnow()
    
    # Base query
    query = Auction.query.filter_by(seller_id=current_user.id)
    
    # Apply status filter
    if status == 'active':
        query = query.filter(Auction.end_time > current_time, Auction.is_active == True)
    elif status == 'ended':
        query = query.filter(Auction.end_time <= current_time)
    elif status == 'all':
        pass  # No additional filtering
    
    # Apply sorting
    query = query.order_by(Auction.created_at.desc())
    
    # Get the auctions
    auctions = query.all()
    
    return render_template('user/my_auctions.html', auctions=auctions, status=status, current_time=current_time)

@user_bp.route('/my-bids')
@login_required
def my_bids():
    # Get bid status filter
    status = request.args.get('status', 'active')
    
    # Get current time for comparison
    current_time = datetime.utcnow()
    
    # Get all bids by this user
    bids = Bid.query.filter_by(bidder_id=current_user.id).order_by(Bid.created_at.desc()).all()
    
    # Group bids by auction
    auctions_bid_on = {}
    
    for bid in bids:
        auction_id = bid.auction_id
        if auction_id not in auctions_bid_on:
            auction = Auction.query.get(auction_id)
            
            # Apply status filter
            if status == 'active' and (auction.end_time <= current_time or not auction.is_active):
                continue
            elif status == 'won' and (auction.end_time > current_time or auction.highest_bidder.id != current_user.id):
                continue
            elif status == 'lost' and (auction.end_time > current_time or auction.highest_bidder is None or auction.highest_bidder.id == current_user.id):
                continue
            
            # Get highest bid
            highest_bid = Bid.query.filter_by(auction_id=auction_id).order_by(Bid.amount.desc()).first()
            
            # Get user's highest bid
            user_highest_bid = Bid.query.filter_by(auction_id=auction_id, bidder_id=current_user.id).order_by(Bid.amount.desc()).first()
            
            auctions_bid_on[auction_id] = {
                'auction': auction,
                'highest_bid': highest_bid,
                'user_highest_bid': user_highest_bid,
                'is_highest_bidder': highest_bid and highest_bid.bidder_id == current_user.id,
                'is_ended': auction.end_time <= current_time
            }
    
    return render_template('user/my_bids.html', auctions_bid_on=auctions_bid_on, status=status)

@user_bp.route('/profile/<int:id>')
def profile_view(id):
    """View another user's profile"""
    user = User.query.get_or_404(id)
    
    # Get recent auctions by this user
    recent_auctions = Auction.query.filter_by(seller_id=id).order_by(Auction.created_at.desc()).limit(5).all()
    
    # Get reviews for this user
    reviews = Review.query.filter_by(seller_id=id).order_by(Review.created_at.desc()).limit(3).all()
    avg_rating = user.get_average_rating()
    
    return render_template('user/public_profile.html', 
                          user=user, 
                          recent_auctions=recent_auctions,
                          reviews=reviews,
                          avg_rating=avg_rating,
                          now=datetime.utcnow)

@user_bp.route('/questions')
@login_required
def view_questions():
    """View all questions asked by the user and their answers."""
    questions = Question.query.filter_by(user_id=current_user.id).order_by(Question.created_at.desc()).all()
    return render_template('user/questions.html', questions=questions)

@user_bp.route('/my-questions')
@login_required
def my_questions():
    """View all questions asked by the current user."""
    questions = Question.query.filter_by(user_id=current_user.id).order_by(Question.created_at.desc()).all()
    return render_template('user/my_questions.html', questions=questions)