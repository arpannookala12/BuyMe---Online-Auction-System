from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db, socketio
from app.models import User, Auction, Bid, Question, Answer, Review, Alert
from app.models.notification import Notification
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

@customer_rep_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@customer_rep_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # Prevent deleting admin users or other customer reps
    if user.is_admin or user.is_customer_rep:
        flash('You cannot delete admin users or customer representatives.', 'danger')
        return redirect(url_for('customer_rep.list_users'))
    
    try:
        # Delete all related data
        # Delete user's auctions
        Auction.query.filter_by(seller_id=id).delete()
        # Delete user's bids
        Bid.query.filter_by(bidder_id=id).delete()
        # Delete user's questions
        Question.query.filter_by(user_id=id).delete()
        # Delete user's answers
        Answer.query.filter_by(user_id=id).delete()
        # Delete user's alerts
        Alert.query.filter_by(user_id=id).delete()
        # Delete user's notifications
        Notification.query.filter_by(user_id=id).delete()
        
        # Finally, delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {user.username} has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user.', 'danger')
    
    return redirect(url_for('customer_rep.list_users'))

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
    """View all questions grouped by auction."""
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')
    
    # Base query
    query = Question.query
    
    # Apply status filter
    if status_filter == 'unanswered':
        query = query.filter_by(status='unanswered')
    elif status_filter == 'answered':
        query = query.filter_by(status='answered')
    
    # Apply search filter if provided
    if search_query:
        query = query.filter(Question.text.ilike(f'%{search_query}%'))
    
    # Get all questions ordered by creation date (newest first)
    all_questions = query.order_by(Question.created_at.desc()).all()
    
    # Group questions by auction
    questions_by_auction = {}
    for question in all_questions:
        auction_id = question.auction_id
        if auction_id not in questions_by_auction:
            questions_by_auction[auction_id] = {
                'auction': question.auction,
                'questions': []
            }
        questions_by_auction[auction_id]['questions'].append(question)
    
    return render_template('customer_rep/questions.html', 
                          questions_by_auction=questions_by_auction, 
                          status_filter=status_filter,
                          search_query=search_query)

@customer_rep_bp.route('/questions/<int:question_id>/answer', methods=['POST'])
@login_required
@customer_rep_required
def answer_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    # Check if question is already answered
    if question.status == 'answered':
        flash('This question has already been answered.', 'warning')
        return redirect(url_for('customer_rep.view_questions'))
    
    answer_text = request.form.get('answer_text')
    if not answer_text:
        flash('Answer text is required.', 'danger')
        return redirect(url_for('customer_rep.view_questions'))
    
    try:
        # Create new answer
        answer = Answer(
            question_id=question_id,
            user_id=current_user.id,
            answer_text=answer_text
        )
        db.session.add(answer)
        
        # Update question status
        question.status = 'answered'
        question.updated_at = datetime.utcnow()
        
        # Create notification for the user who asked the question
        notification = Notification(
            user_id=question.user_id,
            type='question_answered',
            message=f'Your question about "{question.auction.title}" has been answered',
            reference_id=question.auction_id
        )
        db.session.add(notification)
        
        db.session.commit()
        
        # Emit socket event to update all users viewing the auction
        socketio.emit('new_answer', {
            'question_id': question.id,
            'auction_id': question.auction_id,
            'user_id': current_user.id,
            'question_user_id': question.user_id,
            'answer_text': answer_text,
            'answer_username': current_user.username,
            'answer_timestamp': datetime.utcnow().isoformat(),
            'auction_title': question.auction.title
        }, room=f'auction_{question.auction_id}')
        
        # Emit notification to the user who asked the question
        socketio.emit('notification', {
            'title': 'Question Answered',
            'message': notification.message,
            'type': notification.type,
            'link': f'/auction/{question.auction_id}'
        }, room=f'user_{question.user_id}')
        
        flash('Answer has been posted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error posting answer: {str(e)}', 'danger')
    
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
        return redirect(url_for('customer_rep.manage_auctions'))
    
    try:
        # Delete all related data in the correct order to avoid integrity errors
        
        # First get all questions for this auction
        questions = Question.query.filter_by(auction_id=auction_id).all()
        
        # Delete answers for these questions
        for question in questions:
            Answer.query.filter_by(question_id=question.id).delete()
        
        # Delete all questions
        Question.query.filter_by(auction_id=auction_id).delete()
        
        # Delete all bids
        Bid.query.filter_by(auction_id=auction_id).delete()
        
        # Delete all notifications related to this auction
        Notification.query.filter_by(reference_id=auction_id).delete()
        
        # Finally, delete the auction
        db.session.delete(auction)
        db.session.commit()
        
        flash('Auction has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting auction: {str(e)}")  # Log error to console
        flash(f'Error deleting auction: {str(e)}', 'danger')
    
    return redirect(url_for('customer_rep.manage_auctions'))

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

@customer_rep_bp.route('/auctions/<int:id>/toggle', methods=['POST'])
@login_required
@customer_rep_required
def toggle_auction(id):
    auction = Auction.query.get_or_404(id)
    
    # Prevent toggling admin's auctions
    if auction.seller.is_admin:
        flash('You cannot modify auctions created by admin users.', 'danger')
        return redirect(url_for('customer_rep.manage_auctions'))
    
    # Prevent toggling ended auctions
    if auction.end_time <= datetime.utcnow():
        flash('You cannot activate/deactivate ended auctions.', 'danger')
        return redirect(url_for('customer_rep.manage_auctions'))
    
    try:
        # Toggle the auction's active status
        auction.is_active = not auction.is_active
        db.session.commit()
        
        status = "activated" if auction.is_active else "deactivated"
        flash(f'Auction has been {status} successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling auction status: {str(e)}', 'danger')
    
    return redirect(url_for('customer_rep.manage_auctions'))