from app import socketio, db
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app.models import Auction, Bid, Alert, Wishlist, User, Question, Answer
from app import db, socketio
import time
import threading
from datetime import datetime, timedelta
from app.models.notification import Notification
from flask import current_app

_monitor_thread = None
_app = None

def background_auction_monitor():
    """Background task to monitor auctions and send notifications."""
    global _app
    if _app is None:
        print("Error: No application context available")
        return
        
    with _app.app_context():
        while True:
            try:
                # Check auctions ending soon (within 5 minutes)
                ending_soon = Auction.query.filter(
                    Auction.end_time <= datetime.utcnow() + timedelta(minutes=5),
                    Auction.end_time > datetime.utcnow(),
                    Auction.is_active == True
                ).all()
                
                for auction in ending_soon:
                    # Notify seller
                    notification = Notification(
                        user_id=auction.seller_id,
                        type='auction_ending',
                        message=f'Your auction "{auction.title}" is ending in less than 5 minutes!',
                        reference_id=auction.id
                    )
                    db.session.add(notification)
                    socketio.emit('notification', {
                        'title': 'Auction Ending Soon',
                        'message': notification.message,
                        'type': notification.type,
                        'link': f'/auction/{auction.id}'
                    }, room=f'user_{auction.seller_id}')
                    
                    # Notify bidders
                    for bid in auction.bids:
                        if bid.bidder_id != auction.seller_id:
                            notification = Notification(
                                user_id=bid.bidder_id,
                                type='auction_ending',
                                message=f'An auction you bid on "{auction.title}" is ending in less than 5 minutes!',
                                reference_id=auction.id
                            )
                            db.session.add(notification)
                            socketio.emit('notification', {
                                'title': 'Auction Ending Soon',
                                'message': notification.message,
                                'type': notification.type,
                                'link': f'/auction/{auction.id}'
                            }, room=f'user_{bid.bidder_id}')
                
                # Check ended auctions
                ended = Auction.query.filter(
                    Auction.end_time <= datetime.utcnow(),
                    Auction.is_active == True
                ).all()
                
                for auction in ended:
                    auction.is_active = False
                    winner = auction.determine_winner()
                    
                    if winner:
                        # Notify winner
                        notification = Notification(
                            user_id=winner.id,
                            type='auction_won',
                            message=f'Congratulations! You won the auction for "{auction.title}"!',
                            reference_id=auction.id
                        )
                        db.session.add(notification)
                        socketio.emit('notification', {
                            'title': 'Auction Won',
                            'message': notification.message,
                            'type': notification.type,
                            'link': f'/auction/{auction.id}'
                        }, room=f'user_{winner.id}')
                        
                        # Notify seller
                        notification = Notification(
                            user_id=auction.seller_id,
                            type='auction_ended',
                            message=f'Your auction "{auction.title}" has ended. The winner is {winner.username}.',
                            reference_id=auction.id
                        )
                        db.session.add(notification)
                        socketio.emit('notification', {
                            'title': 'Auction Ended',
                            'message': notification.message,
                            'type': notification.type,
                            'link': f'/auction/{auction.id}'
                        }, room=f'user_{auction.seller_id}')
                        
                        # Notify other bidders
                        for bid in auction.bids:
                            if bid.bidder_id not in [winner.id, auction.seller_id]:
                                notification = Notification(
                                    user_id=bid.bidder_id,
                                    type='auction_ended',
                                    message=f'The auction "{auction.title}" has ended. You were outbid.',
                                    reference_id=auction.id
                                )
                                db.session.add(notification)
                                socketio.emit('notification', {
                                    'title': 'Auction Ended',
                                    'message': notification.message,
                                    'type': notification.type,
                                    'link': f'/auction/{auction.id}'
                                }, room=f'user_{bid.bidder_id}')
                
                db.session.commit()
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error in auction monitor: {str(e)}")
                time.sleep(60)  # Wait longer on error

def start_background_monitor(app=None):
    """Start the background monitor if it's not already running."""
    global _monitor_thread, _app
    _app = app
    if _monitor_thread is None or not _monitor_thread.is_alive():
        _monitor_thread = threading.Thread(target=background_auction_monitor)
        _monitor_thread.daemon = True
        _monitor_thread.start()

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    if current_user.is_authenticated:
        # Join the user's personal room
        join_room(f'user_{current_user.id}')
        print(f"User {current_user.id} joined their personal room")
        
        # If user is a customer rep, also join that room
        if current_user.is_customer_rep:
            join_room('customer_reps')
            print(f"Customer rep {current_user.id} joined the customer_reps room")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')

@socketio.on('join_auction')
def on_join_auction(data):
    """Join an auction room."""
    auction_id = data.get('auction_id')
    if auction_id:
        join_room(f'auction_{auction_id}')
        emit('status', {'msg': f'Joined auction room {auction_id}'}, room=f'auction_{auction_id}')

@socketio.on('leave_auction')
def on_leave_auction(data):
    """Leave an auction room."""
    auction_id = data.get('auction_id')
    if auction_id:
        leave_room(f'auction_{auction_id}')

@socketio.on('join_customer_rep_room')
def handle_join_customer_rep_room():
    """Handle customer rep joining their room."""
    if current_user.is_authenticated and current_user.is_customer_rep:
        join_room(f'customer_rep_{current_user.id}')
        join_room('customer_reps')  # Join a common room for all customer reps

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """Handle user joining their personal room."""
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')

@socketio.on('new_question')
def handle_new_question(data):
    """Handle new question event."""
    question_id = data.get('question_id')
    auction_id = data.get('auction_id')
    user_id = data.get('user_id')
    question_text = data.get('question_text')
    
    if question_id and auction_id:
        question = Question.query.get(question_id)
        if question:
            # Emit to all users in the auction room
            socketio.emit('new_question', {
                'question_id': question.id,
                'auction_id': auction_id,
                'user_id': user_id,
                'user_username': question.user.username,
                'question_text': question.text,
                'timestamp': question.created_at.isoformat()
            }, room=f'auction_{auction_id}')
            
            # Notify customer reps about the new question
            customer_reps = User.query.filter_by(is_customer_rep=True).all()
            for rep in customer_reps:
                notification = Notification(
                    user_id=rep.id,
                    title='New Question',
                    message=f'New question about auction "{question.auction.title}"',
                    type='new_question',
                    link=f'/auction/{auction_id}'
                )
                db.session.add(notification)
            
            # Send a single notification to all customer reps
            socketio.emit('notification', {
                'title': 'New Question',
                'message': f'New question from {question.user.username} about auction "{question.auction.title}"',
                'type': 'new_question',
                'link': f'/auction/{auction_id}'
            }, room='customer_reps')

@socketio.on('new_answer')
def handle_new_answer(data):
    """Handle new answer event."""
    question_id = data.get('question_id')
    auction_id = data.get('auction_id')
    answer_text = data.get('answer_text')
    
    if question_id and auction_id:
        question = Question.query.get(question_id)
        if question:
            # Emit to all users in the auction room
            socketio.emit('new_answer', {
                'question_id': question.id,
                'auction_id': auction_id,
                'user_id': current_user.id,
                'question_user_id': question.user_id,
                'answer_text': answer_text,
                'answer_username': current_user.username,
                'answer_timestamp': datetime.utcnow().isoformat(),
                'auction_title': question.auction.title
            }, room=f'auction_{auction_id}')
            
            # Notify the user who asked the question
            notification = Notification(
                user_id=question.user_id,
                type='question_answered',
                message=f'Your question about "{question.auction.title}" has been answered',
                reference_id=auction_id
            )
            db.session.add(notification)
            socketio.emit('notification', {
                'title': 'Question Answered',
                'message': notification.message,
                'type': notification.type,
                'link': f'/auction/{auction_id}'
            }, room=f'user_{question.user_id}')

@socketio.on('new_bid')
def handle_new_bid(data):
    """Process a new bid from a user"""
    if not current_user.is_authenticated:
        emit('bid_response', {'status': 'error', 'message': 'You must be logged in to place a bid'})
        return
    
    auction_id = data.get('auction_id')
    bid_amount = data.get('bid_amount')
    auto_bid_limit = data.get('auto_bid_limit')
    
    try:
        bid_amount = float(bid_amount)
        auto_bid_limit = float(auto_bid_limit) if auto_bid_limit else None
    except (ValueError, TypeError):
        emit('bid_response', {'status': 'error', 'message': 'Invalid bid amount'})
        return
    
    auction = Auction.query.get(auction_id)
    if not auction:
        emit('bid_response', {'status': 'error', 'message': 'Auction not found'})
        return
    
    # Check if auction is active and not ended
    current_time = datetime.utcnow()
    if not auction.is_active or auction.end_time <= current_time:
        emit('bid_response', {'status': 'error', 'message': 'This auction has ended'})
        return
    
    # Check if user is not the seller
    if auction.seller_id == current_user.id:
        emit('bid_response', {'status': 'error', 'message': 'You cannot bid on your own auction'})
        return
    
    # Check if bid is valid (higher than current price + min increment)
    if bid_amount < auction.next_valid_bid_amount():
        emit('bid_response', {
            'status': 'error', 
            'message': f'Bid must be at least ${auction.next_valid_bid_amount():.2f}'
        })
        return
    
    # If auto bid limit is provided, make sure it's greater than the bid amount
    if auto_bid_limit and auto_bid_limit < bid_amount:
        emit('bid_response', {
            'status': 'error', 
            'message': 'Auto-bid limit must be greater than your bid amount'
        })
        return
    
    # Create the bid
    bid = Bid(
        auction_id=auction_id,
        bidder_id=current_user.id,
        amount=bid_amount,
        auto_bid_limit=auto_bid_limit
    )
    db.session.add(bid)
    db.session.commit()
    
    # Process automatic bidding
    from app.routes.auction import process_auto_bidding
    process_auto_bidding(auction)
    
    # Get updated auction data
    auction = Auction.query.get(auction_id)
    highest_bid = Bid.query.filter_by(auction_id=auction_id).order_by(Bid.amount.desc()).first()
    
    # Broadcast the updated auction data to all clients in the auction room
    room = f"auction_{auction_id}"
    emit('bid_update', {
        'status': 'success',
        'auction_id': auction_id,
        'current_price': auction.current_price,
        'next_min_bid': auction.next_valid_bid_amount(),
        'highest_bidder_id': highest_bid.bidder_id if highest_bid else None,
        'highest_bidder_username': highest_bid.bidder.username if highest_bid else None,
        'num_bids': auction.num_bids,
        'your_bid': {'status': 'success', 'amount': bid_amount}
    }, room=room)
    
    # Notify the outbid user if applicable
    second_highest_bid = Bid.query.filter(
        Bid.auction_id == auction_id,
        Bid.bidder_id != current_user.id,
        Bid.amount < bid_amount
    ).order_by(Bid.amount.desc()).first()
    
    if second_highest_bid:
        outbid_room = f"user_{second_highest_bid.bidder_id}"
        emit('outbid_notification', {
            'auction_id': auction_id,
            'auction_title': auction.title,
            'your_bid': second_highest_bid.amount,
            'new_highest_bid': bid_amount
        }, room=outbid_room)

def notify_auction_closed(auction_id, winner_id):
    """Emit an 'auction_closed' event to everyone in that auction's room."""
    socketio.emit(
        'auction_closed',
        {
            'auction_id': auction_id,
            'winner_id':   winner_id
        },
        room=f'auction_{auction_id}'
    )

def notify_winner(auction_id, winner_id):
    """Emit a private 'winner_notification' to the winning user's room."""
    if not winner_id:
        return

    socketio.emit(
        'winner_notification',
        {
          'auction_id': auction_id,
          'message':    'Congratulations! You won this auction.'
        },
        room=f'user_{winner_id}'
    )

def emit_new_bid(auction_id, bid):
    """Emit a new bid event to all users in the auction room."""
    bid_data = {
        'bidder': bid.bidder.username,
        'amount': bid.amount,
        'created_at': bid.created_at.isoformat(),
        'is_auto_bid': bid.is_auto_bid,
        'total_bids': Bid.query.filter_by(auction_id=auction_id).count()
    }
    emit('new_bid', bid_data, room=f'auction_{auction_id}')

def emit_notification(user_id, notification_data):
    """Emit a notification to a specific user."""
    emit('notification', notification_data, room=f'user_{user_id}')

def emit_auction_ended(auction_id):
    """Emit an auction ended event to all users in the auction room."""
    auction = Auction.query.get(auction_id)
    if auction:
        winner = auction.determine_winner()
        end_data = {
            'auction_id': auction_id,
            'title': auction.title,
            'winner': winner.username if winner else None,
            'end_time': datetime.utcnow().isoformat()
        }
        emit('auction_ended', end_data, room=f'auction_{auction_id}')