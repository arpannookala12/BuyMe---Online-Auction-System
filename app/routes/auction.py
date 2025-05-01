from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db, socketio
from app.models import Auction, Item, Bid, Category, Alert, User, Question, Answer, Review
from app.models.notification import Notification
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.tasks import send_notification_email
from werkzeug.utils import secure_filename
import os
from flask import current_app
from flask_socketio import emit
import json

auction_bp = Blueprint('auction', __name__, url_prefix='/auction')

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Ensure the upload folder exists."""
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder

@auction_bp.route('/browse')
def browse():
    """Browse and filter auctions with pagination."""
    # Get filters from query parameters
    category_id = request.args.get('category_id', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    status = request.args.get('status', 'active')
    sort_by = request.args.get('sort', 'end_time_asc')
    search_query = request.args.get('q', '')
    
    # Base query and current time
    current_time = datetime.utcnow()
    query = Auction.query
    
    # Search query
    if search_query:
        query = query.join(Item).filter(
            or_(
                Auction.title.ilike(f'%{search_query}%'),
                Auction.description.ilike(f'%{search_query}%'),
                Item.name.ilike(f'%{search_query}%'),
                Item.description.ilike(f'%{search_query}%')
            )
        )
    
    # Category and subcategories filter
    if category_id:
        category = Category.query.get_or_404(category_id)
        category_ids = [category.id]
        def get_subcats(cat):
            for sub in Category.query.filter_by(parent_id=cat.id).all():
                category_ids.append(sub.id)
                get_subcats(sub)
        get_subcats(category)
        query = query.join(Item).filter(Item.category_id.in_(category_ids))
    
    # Price filters
    if min_price is not None:
        query = query.filter(Auction.initial_price >= min_price)
    if max_price is not None:
        query = query.filter(Auction.initial_price <= max_price)
        
    # Status filter
    if status == 'active':
        query = query.filter(Auction.is_active == True, Auction.end_time > current_time)
    elif status == 'ended':
        query = query.filter(Auction.end_time <= current_time)
    # 'all' shows everything
    
    # Sorting
    if sort_by == 'end_time_asc':
        query = query.order_by(Auction.end_time.asc())
    elif sort_by == 'end_time_desc':
        query = query.order_by(Auction.end_time.desc())
    elif sort_by == 'price_asc':
        query = query.order_by(Auction.initial_price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Auction.initial_price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Auction.created_at.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 16
    auctions = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Top-level categories for sidebar
    categories = Category.query.filter_by(parent_id=None).all()
    
    return render_template('auction/browse.html', auctions=auctions,
                           categories=categories, category_id=category_id,
                           min_price=min_price, max_price=max_price,
                           status=status, sort_by=sort_by,
                           search_query=search_query)

@auction_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new auction and its associated item."""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        initial_price = float(request.form.get('initial_price'))
        min_bid_increment = float(request.form.get('min_increment'))
        reserve_price = float(request.form.get('secret_min_price', 0))
        duration_value = int(request.form.get('duration_value'))
        duration_unit = request.form.get('duration_unit')
        
        # Get all attributes (both required and custom)
        attributes = {}
        
        # Add required attributes
        for key, value in request.form.items():
            if key.startswith('attribute_') and value:
                attr_name = key.replace('attribute_', '')
                attributes[attr_name] = value.strip()
        
        # Add custom attributes
        custom_names = request.form.getlist('custom_attribute_names[]')
        custom_values = request.form.getlist('custom_attribute_values[]')
        for name, value in zip(custom_names, custom_values):
            if name and value:  # Only add if both name and value are provided
                attributes[name.strip()] = value.strip()
        
        # Validate duration and set end time
        now = datetime.utcnow()
        if duration_unit == 'minutes':
            if duration_value < 5:
                flash('Minimum duration is 5 minutes', 'error')
                return redirect(url_for('auction.create'))
            end_time = now + timedelta(minutes=duration_value)
        elif duration_unit == 'hours':
            if duration_value < 1:
                flash('Minimum duration is 1 hour', 'error')
                return redirect(url_for('auction.create'))
            end_time = now + timedelta(hours=duration_value)
        else:  # days
            if duration_value < 1:
                flash('Minimum duration is 1 day', 'error')
                return redirect(url_for('auction.create'))
            if duration_value > 30:
                flash('Maximum duration is 30 days', 'error')
                return redirect(url_for('auction.create'))
            end_time = now + timedelta(days=duration_value)
        
        # Validate reserve price
        if reserve_price > 0 and reserve_price < initial_price:
            flash('Reserve price must be greater than or equal to initial price', 'error')
            return redirect(url_for('auction.create'))
        
        # Create item first
        item = Item(
            name=title,
            description=description,
            category_id=category_id,
            attributes=json.dumps(attributes)  # Store all attributes as JSON
        )
        db.session.add(item)
        db.session.flush()  # Get the item ID without committing
        
        # Handle image upload
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_folder = ensure_upload_folder()
                image_path = os.path.join(upload_folder, filename)
                image.save(image_path)
                # Set the image URL with the correct static path
                item.image_url = f'/static/uploads/{filename}'
        
        # Create auction with exact timestamps
        auction = Auction(
            title=title,
            description=description,
            item_id=item.id,  # Link to the created item
            seller_id=current_user.id,
            initial_price=initial_price,
            min_increment=min_bid_increment,
            secret_min_price=reserve_price,
            start_time=now,  # Set exact start time
            end_time=end_time,  # Set exact end time
            is_active=True  # Ensure auction starts as active
        )
        
        # Save both item and auction
        db.session.add(auction)
        db.session.commit()
        
        # Check for matching alerts
        alerts = Alert.query.filter_by(is_active=True).all()
        for alert in alerts:
            if alert.matches_auction(auction):
                notification = Notification(
                    user_id=alert.user_id,
                    type='alert_match',
                    message=f'New auction matches your alert: "{auction.title}"',
                    reference_id=auction.id
                )
                db.session.add(notification)
                emit_notification(alert.user_id, {
                    'title': 'Alert Match',
                    'message': notification.message,
                    'type': notification.type,
                    'link': url_for('auction.view', id=auction.id)
                })
        
        db.session.commit()
        flash('Auction created successfully!', 'success')
        return redirect(url_for('auction.view', id=auction.id))
    
    # GET request - show the create form with categories
    categories = Category.query.filter_by(parent_id=None).all()
    # Eager load subcategories to avoid N+1 queries
    for category in categories:
        _ = [s for s in category.subcategories]  # Force load subcategories
        for subcategory in category.subcategories:
            _ = [s for s in subcategory.subcategories]  # Force load sub-subcategories
    return render_template('auction/create.html', categories=categories)

@auction_bp.route('/<int:id>')
def view(id):
    """View auction details."""
    auction = Auction.query.get_or_404(id)
    
    # Check auction status
    winner = auction.check_status()
    if winner and not auction.winner_notified:
        # Send notification to winner
        notification = Notification(
            user_id=winner.id,
            type='auction_won',
            message=f'Congratulations! You have won the auction for "{auction.title}"!',
            reference_id=auction.id
        )
        db.session.add(notification)
        
        # Send notification to seller
        seller_notification = Notification(
            user_id=auction.seller_id,
            type='auction_ended',
            message=f'Your auction "{auction.title}" has ended. The winner is {winner.username}.',
            reference_id=auction.id
        )
        db.session.add(seller_notification)
        
        auction.winner_notified = True
        db.session.commit()
        
        # Send real-time notifications
        socketio.emit('notification', {
            'title': 'Auction Won',
            'message': notification.message,
            'type': notification.type,
            'link': url_for('auction.view', id=auction.id)
        }, room=f'user_{winner.id}')
        
        socketio.emit('notification', {
            'title': 'Auction Ended',
            'message': seller_notification.message,
            'type': seller_notification.type,
            'link': url_for('auction.view', id=auction.id)
        }, room=f'user_{auction.seller_id}')
    
    bids = auction.get_bid_history()
    is_ended = auction.is_ended
    seller_rating = Review.get_seller_rating(auction.seller_id)
    
    # Similar active auctions in same category
    similar_items = auction.get_similar_auctions()
    
    return render_template('auction/view.html', auction=auction,
                           bids=bids, is_ended=is_ended,
                           similar_items=similar_items,
                           Review=Review,
                           seller_rating=seller_rating)

@auction_bp.route('/<int:id>/bid', methods=['POST'])
@login_required
def place_bid(id):
    """Handle manual and automatic (proxy) bids."""
    auction = Auction.query.get_or_404(id)
    now = datetime.utcnow()
    if not auction.is_active or auction.end_time <= now:
        flash('This auction has ended.', 'danger')
        return redirect(url_for('auction.view', id=id))
    if auction.seller_id == current_user.id:
        flash('You cannot bid on your own auction.', 'danger')
        return redirect(url_for('auction.view', id=id))

    bid_amount = request.form.get('bid_amount', type=float)
    auto_limit = request.form.get('auto_bid_limit', type=float)
    if not bid_amount:
        flash('Enter a valid bid amount.', 'danger')
        return redirect(url_for('auction.view', id=id))

    # Enforce minimum bid increment
    next_valid = auction.next_valid_bid_amount()
    if bid_amount < next_valid:
        flash(f'Bid must be at least ${next_valid:.2f}.', 'danger')
        return redirect(url_for('auction.view', id=id))
    if auto_limit and auto_limit < bid_amount:
        flash('Auto-bid limit must exceed your bid.', 'danger')
        return redirect(url_for('auction.view', id=id))

    bid = Bid(
        auction_id=id,
        bidder_id=current_user.id,
        amount=bid_amount,
        auto_bid_limit=auto_limit,
        is_auto_bid=False
    )
    db.session.add(bid)
    db.session.commit()

    # Emit new bid event
    socketio.emit('new_bid', {
        'bid_id': bid.id,
        'auction_id': auction.id,
        'bidder_username': current_user.username,
        'amount': bid_amount,
        'created_at': bid.created_at.isoformat(),
        'is_auto_bid': False,
        'is_customer_rep': current_user.is_customer_rep
    }, room=f'auction_{id}')

    # Process automatic bidding
    process_auto_bidding(auction)
    
    # Notify other bidders
    notify_other_bidders(auction, bid)
    
    flash('Your bid has been placed.', 'success')
    return redirect(url_for('auction.view', id=id))

def process_auto_bidding(auction):
    """Process automatic bidding (proxy bidding) for an auction."""
    # Get current highest bid
    highest = Bid.query.filter_by(auction_id=auction.id).order_by(Bid.amount.desc()).first()
    if not highest:
        return

    # Get all active auto-bids
    auto_bids = (
        Bid.query
           .filter(
               Bid.auction_id == auction.id,
               Bid.auto_bid_limit.isnot(None)
           )
           .order_by(Bid.auto_bid_limit.desc())
           .all()
    )
    
    if not auto_bids:
        return

    # Process auto-bids
    current_price = highest.amount
    for bid in auto_bids:
        if bid.bidder_id == highest.bidder_id:
            continue
            
        if bid.auto_bid_limit > current_price:
            new_amount = min(
                bid.auto_bid_limit,
                current_price + auction.min_increment
            )
            
            if new_amount > current_price:
                # Get the bidder to ensure they exist
                bidder = User.query.get(bid.bidder_id)
                if not bidder:
                    continue  # Skip if bidder doesn't exist
                    
                new_bid = Bid(
                    auction_id=auction.id,
                    bidder_id=bid.bidder_id,
                    amount=new_amount,
                    auto_bid_limit=bid.auto_bid_limit,
                    is_auto_bid=True
                )
                db.session.add(new_bid)
                db.session.flush()  # Get the ID and created_at without committing
                current_price = new_amount
                
                # Emit new auto-bid event
                socketio.emit('new_bid', {
                    'bid_id': new_bid.id,
                    'auction_id': auction.id,
                    'bidder_username': bidder.username,
                    'amount': new_amount,
                    'created_at': new_bid.created_at.isoformat() if new_bid.created_at else datetime.utcnow().isoformat(),
                    'is_auto_bid': True,
                    'is_customer_rep': bidder.is_customer_rep
                }, room=f'auction_{auction.id}')
                
                # Create notification for auto-bid
                notification = Notification(
                    user_id=bid.bidder_id,
                    type='auto_bid',
                    message=f'Your auto-bid of ${new_amount:.2f} was placed on auction "{auction.title}"',
                    reference_id=auction.id
                )
                db.session.add(notification)
                
                # Send real-time notification
                socketio.emit('user_notification', {
                    'title': 'Auto-bid Placed',
                    'message': notification.message,
                    'type': 'info',
                    'link': url_for('auction.view', id=auction.id)
                }, room=f'user_{bid.bidder_id}')
                
                # Notify if auto-bid limit is reached
                if new_amount >= bid.auto_bid_limit:
                    notification = Notification(
                        user_id=bid.bidder_id,
                        type='auto_bid_limit',
                        message=f'Your auto-bid limit of ${bid.auto_bid_limit:.2f} has been reached for auction "{auction.title}"',
                        reference_id=auction.id
                    )
                    db.session.add(notification)
                    
                    # Send real-time notification
                    socketio.emit('user_notification', {
                        'title': 'Auto-bid Limit Reached',
                        'message': notification.message,
                        'type': 'warning',
                        'link': url_for('auction.view', id=auction.id)
                    }, room=f'user_{bid.bidder_id}')
    
    db.session.commit()

def notify_other_bidders(auction, new_bid):
    """Notify other bidders about new bids."""
    other_bidders = set()
    for bid in auction.bids:
        if bid.bidder_id != new_bid.bidder_id:
            other_bidders.add(bid.bidder)
    
    for bidder in other_bidders:
        # Create notification
        notification = Notification(
            user_id=bidder.id,
            type='outbid',
            message=f'You have been outbid on auction "{auction.title}". New bid: ${new_bid.amount:.2f}',
            reference_id=auction.id
        )
        db.session.add(notification)
        
        # Send real-time notification
        socketio.emit('user_notification', {
            'title': 'You Have Been Outbid',
            'message': notification.message,
            'type': 'warning',
            'link': url_for('auction.view', id=auction.id)
        }, room=f'user_{bidder.id}')
    
    db.session.commit()

@auction_bp.route('/<int:id>/history')
def bid_history(id):
    """View complete bid history for an auction."""
    auction = Auction.query.get_or_404(id)
    bids = auction.get_bid_history()
    return render_template('auction/history.html', auction=auction, bids=bids)

@auction_bp.route('/user/<int:user_id>/auctions')
@login_required
def user_auctions(user_id):
    """View all auctions a user has participated in."""
    user = User.query.get_or_404(user_id)
    auctions_bid_on = (
        Auction.query
               .join(Bid)
               .filter(Bid.bidder_id == user_id)
               .distinct()
               .all()
    )
    auctions_sold = Auction.query.filter_by(seller_id=user_id).all()
    return render_template('auction/user_auctions.html',
                           user=user,
                           auctions_bid_on=auctions_bid_on,
                           auctions_sold=auctions_sold)

@auction_bp.route('/<int:id>/end', methods=['POST'])
@login_required
def end_auction(id):
    """End an auction early (admin/customer rep only)."""
    if not current_user.is_admin and not current_user.is_customer_rep:
        abort(403)
        
    auction = Auction.query.get_or_404(id)
    if not auction.is_active:
        flash('Auction is already ended.', 'warning')
        return redirect(url_for('auction.view', id=id))
        
    auction.is_active = False
    auction.end_time = datetime.utcnow()
    winner = auction.determine_winner()
    
    if winner:
        send_notification_email(
            winner.email,
            'Auction Won',
            f'Congratulations! You have won the auction for "{auction.title}"!'
        )
        send_notification_email(
            auction.seller.email,
            'Auction Ended',
            f'Your auction "{auction.title}" has ended. The winner is {winner.username}.'
        )
    else:
        send_notification_email(
            auction.seller.email,
            'Auction Ended',
            f'Your auction "{auction.title}" has ended. No winner was determined.'
        )
    
    db.session.commit()
    flash('Auction ended successfully.', 'success')
    return redirect(url_for('auction.view', id=id))

@auction_bp.route('/auction/<int:auction_id>/question', methods=['POST'])
@login_required
def ask_question(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    
    # Check if auction is active
    if not auction.is_active:
        flash('Cannot ask questions on inactive auctions', 'error')
        return redirect(url_for('auction.view', id=auction_id))
    
    question_text = request.form.get('question_text')
    
    if not question_text:
        flash('Question text is required', 'error')
        return redirect(url_for('auction.view', id=auction_id))
    
    question = Question(
        user_id=current_user.id,
        auction_id=auction_id,
        question_text=question_text
    )
    db.session.add(question)
    db.session.commit()
    
    flash('Your question has been posted', 'success')
    return redirect(url_for('auction.view', id=auction_id))

@auction_bp.route('/question/<int:question_id>/answer', methods=['POST'])
@login_required
def answer_question(question_id):
    question = Question.query.get_or_404(question_id)
    auction = question.auction
    
    if current_user.id != auction.seller_id and not current_user.is_customer_rep:
        flash('You are not authorized to answer this question.', 'danger')
        return redirect(url_for('auction.view', id=auction.id))
    
    answer_text = request.form.get('answer_text')
    if not answer_text:
        flash('Answer text is required.', 'danger')
        return redirect(url_for('auction.view', id=auction.id))
    
    answer = Answer(
        question_id=question_id,
        user_id=current_user.id,
        answer_text=answer_text
    )
    
    db.session.add(answer)
    question.is_answered = True
    db.session.commit()
    
    # Emit socket event for new answer
    socketio.emit('new_answer', {
        'question_id': question_id,
        'answer': {
            'id': answer.id,
            'text': answer_text,
            'username': current_user.username,
            'is_customer_rep': current_user.is_customer_rep,
            'created_at': answer.created_at.isoformat()
        }
    }, room=f'auction_{auction.id}')
    
    flash('Your answer has been posted.', 'success')
    return redirect(url_for('auction.view', id=auction.id))
