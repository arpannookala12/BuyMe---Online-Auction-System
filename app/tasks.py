from datetime import datetime
from . import db
from flask import current_app
from .models.auction import Auction
from .models import Bid
from .socket_events import notify_auction_closed, notify_winner
from flask_mail import Message
from app import mail

def finalize_auctions():
    """Scan for ended auctions, finalize them, and send alerts."""
    # Ensure we have app context if APScheduler doesn't automatically push one
    with current_app.app_context():
        now = datetime.utcnow()
        ended = (
            Auction.query
                   .filter(Auction.end_time <= now, Auction.status == 'open')
                   .all()
        )

        for auction in ended:
            auction.status = 'closed'
            highest = (
                Bid.query
                   .filter_by(auction_id=auction.id)
                   .order_by(Bid.amount.desc())
                   .first()
            )

            winner_id = None
            if highest and (auction.reserve_price is None or highest.amount >= auction.reserve_price):
                winner_id = highest.bidder_id

            auction.winner_id = winner_id
            db.session.add(auction)
            db.session.commit()

            notify_auction_closed(auction.id, winner_id)
            if winner_id:
                notify_winner(auction.id, winner_id)

def send_notification_email(to_email, subject, message):
    """Send a notification email to a user."""
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=message,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        return False
