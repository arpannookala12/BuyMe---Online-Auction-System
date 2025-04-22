from flask import Blueprint, render_template, redirect, url_for
from app.models import Auction, Category
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Get featured auctions (recent, ending soon, etc.)
    current_time = datetime.utcnow()
    
    # Recent auctions
    recent_auctions = Auction.query.filter(
        Auction.is_active == True,
        Auction.end_time > current_time
    ).order_by(Auction.created_at.desc()).limit(4).all()
    
    # Ending soon auctions
    ending_soon = Auction.query.filter(
        Auction.is_active == True,
        Auction.end_time > current_time
    ).order_by(Auction.end_time.asc()).limit(4).all()
    
    # Popular auctions (most bids)
    popular_auctions = Auction.query.filter(
        Auction.is_active == True,
        Auction.end_time > current_time
    ).join(Auction.bids).group_by(Auction.id).order_by(
        db.func.count(Bid.id).desc()
    ).limit(4).all()
    
    # Get all top-level categories
    categories = Category.query.filter_by(parent_id=None).all()
    
    return render_template('index.html', 
                          recent_auctions=recent_auctions,
                          ending_soon=ending_soon,
                          popular_auctions=popular_auctions,
                          categories=categories)

# Import these at the bottom to avoid circular imports
from app import db
from app.models import Bid