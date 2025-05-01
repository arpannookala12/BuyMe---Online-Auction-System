from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Auction, Bid, Question, Answer, Review
from datetime import datetime,timezone
from functools import wraps

customer_rep_bp = Blueprint('customer_rep', __name__, url_prefix='/customer_rep')

def customer_rep_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_customer_rep:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@customer_rep_bp.route('/dashboard')
@login_required
@customer_rep_required
def dashboard():
    # Get basic statistics
    user_count = User.query.filter_by(is_admin=False, is_customer_rep=False).count()
    active_auctions = Auction.query.filter_by(is_active=True).count()
    total_bids = Bid.query.count()
    current_time = datetime.utcnow()
    # Get recent auctions
    recent_auctions = Auction.query.order_by(Auction.created_at.desc()).limit(10).all()
    
    return render_template('customer_rep/dashboard.html', 
                          user_count=user_count,
                          active_auctions=active_auctions,
                          total_bids=total_bids,
                          recent_auctions=recent_auctions,
                          current_time=current_time)

@customer_rep_bp.route('/users')
@login_required
@customer_rep_required
def list_users():
    users = User.query.filter(User.is_admin == False).all()
    return render_template('customer_rep/users.html', users=users)

@customer_rep_bp.route('/users/<int:id>')
@login_required
@customer_rep_required
def view_user(id):
    user = User.query.get_or_404(id)
    if user.is_admin:
        flash('You cannot view admin user details.', 'danger')
        return redirect(url_for('customer_rep.list_users'))
    auctions = Auction.query.filter_by(seller_id=id).all()
    bids = Bid.query.filter_by(bidder_id=id).all()
    questions = Question.query.filter_by(user_id=id).all()
    return render_template('customer_rep/user_detail.html', 
                         user=user, 
                         auctions=auctions, 
                         bids=bids,
                         questions=questions)

@customer_rep_bp.route('/users/<int:id>/disable', methods=['POST'])
@login_required
@customer_rep_required
def disable_user(id):
    user = User.query.get_or_404(id)
    
    # Prevent disabling admin users
    if user.is_admin:
        flash('You cannot disable admin users.', 'danger')
        return redirect(url_for('customer_rep.list_users'))
    
    try:
        # Update the user's active status
        user.active = False
        db.session.commit()
        flash(f'User {user.username} has been disabled.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error disabling user.', 'danger')
    
    return redirect(url_for('customer_rep.view_user', id=id))

@customer_rep_bp.route('/users/<int:id>/enable', methods=['POST'])
@login_required
@customer_rep_required
def enable_user(id):
    user = User.query.get_or_404(id)
    
    # Prevent enabling admin users (though this shouldn't be necessary)
    if user.is_admin:
        flash('You cannot modify admin users.', 'danger')
        return redirect(url_for('customer_rep.list_users'))
    
    try:
        # Update the user's active status
        user.active = True
        db.session.commit()
        flash(f'User {user.username} has been enabled.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error enabling user.', 'danger')
    
    return redirect(url_for('customer_rep.view_user', id=id))

@customer_rep_bp.route('/questions')
@login_required
@customer_rep_required
def view_questions():
    """View all unanswered questions."""
    questions = Question.query.filter_by(is_answered=False).order_by(Question.created_at.desc()).all()
    return render_template('customer_rep/questions.html', questions=questions)

@customer_rep_bp.route('/questions/<int:question_id>/answer', methods=['POST'])
@login_required
@customer_rep_required
def answer_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    answer_text = request.form.get('answer_text')
    if not answer_text:
        flash('Answer text is required.', 'danger')
        return redirect(url_for('customer_rep.view_questions'))
    
    try:
        question.answer_text = answer_text
        question.answered_by = current_user
        question.answered_at = db.func.now()
        db.session.commit()
        flash('Answer has been posted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error posting answer.', 'danger')
    
    return redirect(url_for('customer_rep.view_questions'))

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
    
    current_time = datetime.utcnow()
    
    return render_template('customer_rep/auctions.html', 
                         auctions=auctions, 
                         search=search,
                         current_time=current_time)

@customer_rep_bp.route('/auctions/<int:auction_id>/delete', methods=['POST'])
@login_required
@customer_rep_required
def delete_auction(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    
    # Prevent deleting admin's auctions
    if auction.seller.is_admin:
        flash('You cannot delete auctions created by admin users.', 'danger')
        return redirect(url_for('customer_rep.view_questions'))
    
    try:
        # Delete all related bids first
        Bid.query.filter_by(auction_id=auction_id).delete()
        db.session.delete(auction)
        db.session.commit()
        flash('Auction has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting auction.', 'danger')
    
    return redirect(url_for('customer_rep.view_questions'))

@customer_rep_bp.route('/bids/<int:bid_id>/delete', methods=['POST'])
@login_required
@customer_rep_required
def delete_bid(bid_id):
    bid = Bid.query.get_or_404(bid_id)
    
    # Prevent deleting bids from admin users
    if bid.bidder.is_admin:
        flash('Cannot delete bids from admin users.', 'danger')
        return redirect(url_for('customer_rep.view_questions'))
    
    db.session.delete(bid)
    db.session.commit()
    
    flash('Bid deleted successfully.', 'success')
    return redirect(url_for('customer_rep.view_questions'))