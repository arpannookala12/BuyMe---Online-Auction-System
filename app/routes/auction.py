from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Auction, Item, Bid, Category, Alert, User
from datetime import datetime, timedelta

auction_bp = Blueprint('auction', __name__, url_prefix='/auction')

@auction_bp.route('/browse')
def browse():
    # Get filters from query parameters
    category_id = request.args.get('category_id', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    status = request.args.get('status', 'active')
    sort_by = request.args.get('sort', 'end_time_asc')
    
    # Base query
    current_time = datetime.utcnow()
    query = Auction.query
    
    # Apply filters
    if category_id:
        category = Category.query.get_or_404(category_id)
        # Get all subcategory IDs
        category_ids = [category_id]
        
        def get_subcategory_ids(cat_id):
            subcats = Category.query.filter_by(parent_id=cat_id).all()
            for subcat in subcats:
                category_ids.append(subcat.id)
                get_subcategory_ids(subcat.id)
        
        get_subcategory_ids(category_id)
        
        # Filter by all categories and subcategories
        query = query.join(Item).filter(Item.category_id.in_(category_ids))
    
    if min_price is not None:
        query = query.filter(Auction.initial_price >= min_price)
    
    if max_price is not None:
        query = query.filter(Auction.initial_price <= max_price)
        
    # Apply status filter
    if status == 'active':
        query = query.filter(Auction.is_active == True, 
                            Auction.end_time > current_time)
    elif status == 'ended':
        query = query.filter(Auction.end_time <= current_time)
    elif status == 'all':
        pass  # No additional filtering
    
    # Apply sorting
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
    
    # Get all top-level categories for filter sidebar
    categories = Category.query.filter_by(parent_id=None).all()
    
    return render_template('auction/browse.html', 
                          auctions=auctions,
                          categories=categories,
                          category_id=category_id,
                          min_price=min_price,
                          max_price=max_price,
                          status=status,
                          sort_by=sort_by)

@auction_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id', type=int)
        initial_price = request.form.get('initial_price', type=float)
        min_increment = request.form.get('min_increment', type=float)
        secret_min_price = request.form.get('secret_min_price', type=float)
        duration_days = request.form.get('duration_days', type=int)
        
        # Form validation
        if not all([title, description, category_id, initial_price, min_increment, duration_days]):
            flash('All fields are required', 'danger')
            categories = Category.query.all()
            return render_template('auction/create.html', categories=categories)
        
        if secret_min_price < initial_price:
            flash('Secret minimum price must be at least the initial price', 'danger')
            categories = Category.query.all()
            return render_template('auction/create.html', categories=categories)
        
        # Create item
        item_name = request.form.get('item_name', title)  # Use title as item name if not provided
        item = Item(name=item_name, description=description, category_id=category_id)
        
        # Get custom attributes based on category
        category = Category.query.get(category_id)
        attributes = {}
        # In a real app, you would dynamically get the attributes for this category
        # For now, we'll just use any attribute_ prefixed form fields
        for key, value in request.form.items():
            if key.startswith('attribute_') and value:
                attr_name = key[10:]  # Remove 'attribute_' prefix
                attributes[attr_name] = value
        
        item.set_attributes(attributes)
        db.session.add(item)
        
        # Create auction
        end_time = datetime.utcnow() + timedelta(days=duration_days)
        auction = Auction(
            item=item,
            seller=current_user,
            title=title,
            description=description,
            initial_price=initial_price,
            min_increment=min_increment,
            secret_min_price=secret_min_price,
            end_time=end_time
        )
        db.session.add(auction)
        db.session.commit()
        
        # Check for matching alerts and notify users
        matching_alerts = Alert.query.filter_by(is_active=True).all()
        for alert in matching_alerts:
            if alert.matches_item(item, auction):
                # In a real app, send email notification
                # For now, just create a flash message
                flash(f'Alert notification sent to user {alert.user_id}', 'info')
        
        flash('Auction created successfully!', 'success')
        return redirect(url_for('auction.view', id=auction.id))
    
    # GET request - show the create form
    categories = Category.query.all()
    return render_template('auction/create.html', categories=categories)

@auction_bp.route('/<int:id>')
def view(id):
    auction = Auction.query.get_or_404(id)
    
    # Get bid history
    bids = Bid.query.filter_by(auction_id=id).order_by(Bid.created_at.desc()).all()
    
    # Check if auction has ended
    is_ended = datetime.utcnow() > auction.end_time
    
    # Get similar items
    similar_items = []
    if auction.item and auction.item.category_id:
        similar_auctions = Auction.query.join(Item).filter(
            Item.category_id == auction.item.category_id,
            Auction.id != auction.id,
            Auction.is_active == True,
            Auction.end_time > datetime.utcnow()
        ).limit(4).all()
        similar_items = similar_auctions
    
    return render_template('auction/view.html', 
                          auction=auction,
                          bids=bids,
                          is_ended=is_ended,
                          similar_items=similar_items)

@auction_bp.route('/<int:id>/bid', methods=['POST'])
@login_required
def place_bid(id):
    auction = Auction.query.get_or_404(id)
    
    # Check if auction is active and not ended
    current_time = datetime.utcnow()
    if not auction.is_active or auction.end_time <= current_time:
        flash('This auction has ended', 'danger')
        return redirect(url_for('auction.view', id=id))
    
    # Check if user is not the seller
    if auction.seller_id == current_user.id:
        flash('You cannot bid on your own auction', 'danger')
        return redirect(url_for('auction.view', id=id))
    
    # Get bid amount
    bid_amount = request.form.get('bid_amount', type=float)
    auto_bid_limit = request.form.get('auto_bid_limit', type=float)
    
    if not bid_amount:
        flash('Please enter a valid bid amount', 'danger')
        return redirect(url_for('auction.view', id=id))
    
    # Check if bid is valid (higher than current price + min increment)
    if bid_amount < auction.next_valid_bid_amount():
        flash(f'Bid must be at least ${auction.next_valid_bid_amount():.2f}', 'danger')
        return redirect(url_for('auction.view', id=id))
    
    # If auto bid limit is provided, make sure it's greater than the bid amount
    if auto_bid_limit and auto_bid_limit < bid_amount:
        flash('Auto-bid limit must be greater than your bid amount', 'danger')
        return redirect(url_for('auction.view', id=id))
    
    # Create the bid
    bid = Bid(
        auction_id=id,
        bidder_id=current_user.id,
        amount=bid_amount,
        auto_bid_limit=auto_bid_limit
    )
    db.session.add(bid)
    db.session.commit()
    
    # Process automatic bidding
    process_auto_bidding(auction)
    
    flash('Your bid has been placed successfully!', 'success')
    return redirect(url_for('auction.view', id=id))

def process_auto_bidding(auction):
    """Process automatic bidding for an auction"""
    # Get all auto bids for this auction, ordered by auto_bid_limit (highest first)
    auto_bids = Bid.query.filter(
        Bid.auction_id == auction.id,
        Bid.auto_bid_limit.isnot(None)
    ).order_by(Bid.auto_bid_limit.desc()).all()
    
    if not auto_bids:
        return
    
    # Get current highest bid
    highest_bid = Bid.query.filter_by(auction_id=auction.id).order_by(Bid.amount.desc()).first()
    
    # Check if we have at least 2 auto bids
    if len(auto_bids) >= 2:
        # Get the top two auto-bidders
        highest_auto_bidder = auto_bids[0]
        second_highest_auto_bidder = auto_bids[1]
        
        # If the highest auto bidder is not already the highest bidder
        if highest_auto_bidder.id != highest_bid.id:
            # Place a new bid for the highest auto bidder
            new_bid_amount = min(
                second_highest_auto_bidder.auto_bid_limit + auction.min_increment,
                highest_auto_bidder.auto_bid_limit
            )
            
            # Make sure it's higher than the current highest bid
            new_bid_amount = max(new_bid_amount, highest_bid.amount + auction.min_increment)
            
            # Only place a new bid if it's within the limit
            if new_bid_amount <= highest_auto_bidder.auto_bid_limit:
                new_bid = Bid(
                    auction_id=auction.id,
                    bidder_id=highest_auto_bidder.bidder_id,
                    amount=new_bid_amount,
                    auto_bid_limit=highest_auto_bidder.auto_bid_limit
                )
                db.session.add(new_bid)
                db.session.commit()
    
    # Handle the case where there's only one auto bidder
    elif len(auto_bids) == 1 and highest_bid.id != auto_bids[0].id:
        auto_bidder = auto_bids[0]
        new_bid_amount = highest_bid.amount + auction.min_increment
        
        if new_bid_amount <= auto_bidder.auto_bid_limit:
            new_bid = Bid(
                auction_id=auction.id,
                bidder_id=auto_bidder.bidder_id,
                amount=new_bid_amount,
                auto_bid_limit=auto_bidder.auto_bid_limit
            )
            db.session.add(new_bid)
            db.session.commit()