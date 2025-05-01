from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Review, Auction, User
from datetime import datetime

review_bp = Blueprint('review', __name__, url_prefix='/review')

@review_bp.route('/create/<int:auction_id>', methods=['GET', 'POST'])
@login_required
def create(auction_id):
    """Create a review for a completed auction"""
    # Get the auction
    auction = Auction.query.get_or_404(auction_id)
    
    # Check if the auction has ended
    current_time = datetime.utcnow()
    if not auction.end_time <= current_time:
        flash('You can only review completed auctions', 'danger')
        return redirect(url_for('auction.view', id=auction_id))
    
    # Check if the current user is the highest bidder
    if not auction.highest_bidder or auction.highest_bidder.id != current_user.id:
        flash('Only the winning bidder can review the seller', 'danger')
        return redirect(url_for('auction.view', id=auction_id))
    
    # Check if user has already reviewed this auction
    existing_review = Review.query.filter_by(
        auction_id=auction_id, 
        reviewer_id=current_user.id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this auction', 'warning')
        return redirect(url_for('auction.view', id=auction_id))
    
    if request.method == 'POST':
        # Get form data
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment')
        
        # Validate rating
        if not rating or rating < 1 or rating > 5:
            flash('Please provide a rating between 1 and 5', 'danger')
            return render_template('review/create.html', auction=auction)
        
        # Create review
        review = Review(
            auction_id=auction_id,
            reviewer_id=current_user.id,
            seller_id=auction.seller_id,
            rating=rating,
            comment=comment
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Your review has been submitted successfully', 'success')
        return redirect(url_for('auction.view', id=auction_id))
    
    return render_template('review/create.html', auction=auction)

@review_bp.route('/user/<int:user_id>')
def user_reviews(user_id):
    """View all reviews for a specific user"""
    user = User.query.get_or_404(user_id)
    reviews = Review.query.filter_by(seller_id=user_id).order_by(Review.created_at.desc()).all()
    
    # Calculate average rating
    avg_rating = 0
    if reviews:
        avg_rating = sum(review.rating for review in reviews) / len(reviews)
    
    return render_template('review/user_reviews.html', user=user, reviews=reviews, avg_rating=avg_rating)

@review_bp.route('/seller/<int:seller_id>')
def seller_reviews(seller_id):
    reviews = Review.get_seller_reviews(seller_id)
    average_rating = Review.get_seller_rating(seller_id)
    
    return render_template('review/seller_reviews.html',
                         reviews=reviews,
                         average_rating=average_rating,
                         seller_id=seller_id)