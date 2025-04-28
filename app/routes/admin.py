from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Auction, Bid, Category, Item
from sqlalchemy import func
from functools import wraps
from datetime import datetime, timedelta, timezone

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Custom decorator to check if the user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get basic statistics
    user_count = User.query.filter_by(role='user').count()
    rep_count = User.query.filter_by(role='customer_rep').count()
    auction_count = Auction.query.count()
    active_auctions = Auction.query.filter_by(is_active=True).count()
    bid_count = Bid.query.count()
    
    # Get recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_auctions = Auction.query.order_by(Auction.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          user_count=user_count,
                          rep_count=rep_count,
                          auction_count=auction_count,
                          active_auctions=active_auctions,
                          bid_count=bid_count,
                          recent_users=recent_users,
                          recent_auctions=recent_auctions)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    report_type = request.args.get('type', 'earnings')
    time_period = request.args.get('period', 'month')
    
    # Set time range based on period
    now = datetime.utcnow()
    if time_period == 'week':
        start_date = now - timedelta(days=7)
    elif time_period == 'month':
        start_date = now - timedelta(days=30)
    elif time_period == 'year':
        start_date = now - timedelta(days=365)
    else:  # all time
        start_date = datetime.min
    
    # Generate report based on type
    if report_type == 'earnings':
        report_data = generate_earnings_report(start_date)
    elif report_type == 'items':
        report_data = generate_items_report(start_date)
    elif report_type == 'users':
        report_data = generate_users_report(start_date)
    else:
        report_data = {}
    
    return render_template('admin/reports.html', 
                          report_type=report_type,
                          time_period=time_period,
                          report_data=report_data)

@admin_bp.route('/customer-reps')
@login_required
@admin_required
def manage_reps():
    # Get all customer representatives
    customer_reps = User.query.filter_by(role='customer_rep').order_by(User.username).all()
    
    return render_template('admin/customer_reps.html', customer_reps=customer_reps)

@admin_bp.route('/create-rep', methods=['GET', 'POST'])
@login_required
@admin_required
def create_rep():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validate input
        if not username or not email or not password:
            flash('Username, email, and password are required', 'danger')
            return render_template('admin/create_rep.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('admin/create_rep.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('admin/create_rep.html')
        
        # Create new customer representative
        rep = User(
            username=username,
            email=email,
            password=password,  # The model will hash this
            first_name=first_name,
            last_name=last_name,
            role='customer_rep'
        )
        
        db.session.add(rep)
        db.session.commit()
        
        flash('Customer representative created successfully', 'success')
        return redirect(url_for('admin.manage_reps'))
    
    return render_template('admin/create_rep.html')

@admin_bp.route('/category')
@login_required
@admin_required
def manage_categories():
    # Get all top-level categories
    categories = Category.query.filter_by(parent_id=None).all()
    
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/category/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description')
        parent_id = request.form.get('parent_id')
        
        # Validate input
        if not name:
            flash('Category name is required', 'danger')
            categories = Category.query.all()
            return render_template('admin/create_category.html', categories=categories)
        
        # Convert empty string to None
        if parent_id == '':
            parent_id = None
        
        # Create category
        category = Category(
            name=name,
            description=description,
            parent_id=parent_id
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully', 'success')
        return redirect(url_for('admin.manage_categories'))
    
    # Get all categories for parent selection
    categories = Category.query.all()
    return render_template('admin/create_category.html', categories=categories)

# Helper functions for generating reports
def generate_earnings_report(start_date):
    # Get completed auctions (ended and with bids)
    completed_auctions = db.session.query(Auction).filter(
        Auction.end_time <= datetime.utcnow(),
        Auction.end_time >= start_date
    ).join(Bid).group_by(Auction.id).all()
    
    # Calculate total earnings (sum of highest bids)
    total_earnings = 0
    for auction in completed_auctions:
        highest_bid = db.session.query(func.max(Bid.amount)).filter(Bid.auction_id == auction.id).scalar()
        if highest_bid and highest_bid >= auction.secret_min_price:
            total_earnings += highest_bid
    
    # Earnings per item category
    category_earnings = {}
    category_query = db.session.query(
        Category.name,
        func.sum(Bid.amount).label('earnings')
    ).join(
        Item, Category.id == Item.category_id
    ).join(
        Auction, Item.id == Auction.item_id
    ).join(
        Bid, Auction.id == Bid.auction_id
    ).filter(
        Auction.end_time <= datetime.utcnow(),
        Auction.end_time >= start_date,
        Bid.id.in_(
            db.session.query(func.max(Bid.id)).group_by(Bid.auction_id)
        )
    ).group_by(Category.name).all()
    
    for name, earnings in category_query:
        category_earnings[name] = earnings
    
    # Earnings per seller
    seller_earnings = {}
    seller_query = db.session.query(
        User.username,
        func.sum(Bid.amount).label('earnings')
    ).join(
        Auction, User.id == Auction.seller_id
    ).join(
        Bid, Auction.id == Bid.auction_id
    ).filter(
        Auction.end_time <= datetime.utcnow(),
        Auction.end_time >= start_date,
        Bid.id.in_(
            db.session.query(func.max(Bid.id)).group_by(Bid.auction_id)
        )
    ).group_by(User.username).all()
    
    for username, earnings in seller_query:
        seller_earnings[username] = earnings
    
    return {
        'total_earnings': total_earnings,
        'category_earnings': category_earnings,
        'seller_earnings': seller_earnings
    }

def generate_items_report(start_date):
    # Best-selling items (most completed auctions)
    best_selling_items = db.session.query(
        Item.name,
        func.count(Auction.id).label('sales_count')
    ).join(
        Auction, Item.id == Auction.item_id
    ).join(
        Bid, Auction.id == Bid.auction_id
    ).filter(
        Auction.end_time <= datetime.utcnow(),
        Auction.end_time >= start_date,
        Bid.id.in_(
            db.session.query(func.max(Bid.id)).group_by(Bid.auction_id)
        )
    ).group_by(Item.name).order_by(func.count(Auction.id).desc()).limit(10).all()
    
    # Best-selling categories
    best_selling_categories = db.session.query(
        Category.name,
        func.count(Auction.id).label('sales_count')
    ).join(
        Item, Category.id == Item.category_id
    ).join(
        Auction, Item.id == Auction.item_id
    ).join(
        Bid, Auction.id == Bid.auction_id
    ).filter(
        Auction.end_time <= datetime.utcnow(),
        Auction.end_time >= start_date,
        Bid.id.in_(
            db.session.query(func.max(Bid.id)).group_by(Bid.auction_id)
        )
    ).group_by(Category.name).order_by(func.count(Auction.id).desc()).limit(10).all()
    
    # Most valuable items (highest auction closing prices)
    most_valuable_items = db.session.query(
        Item.name,
        Auction.title,
        func.max(Bid.amount).label('highest_bid')
    ).join(
        Auction, Item.id == Auction.item_id
    ).join(
        Bid, Auction.id == Bid.auction_id
    ).filter(
        Auction.end_time <= datetime.utcnow(),
        Auction.end_time >= start_date
    ).group_by(Item.name, Auction.title).order_by(func.max(Bid.amount).desc()).limit(10).all()
    
    return {
        'best_selling_items': best_selling_items,
        'best_selling_categories': best_selling_categories,
        'most_valuable_items': most_valuable_items
    }

def generate_users_report(start_date):
    # Top sellers (by number of completed auctions)
    top_sellers_by_count = db.session.query(
        User.username,
        func.count(Auction.id).label('auction_count')
    ).join(
        Auction, User.id == Auction.seller_id
    ).join(
        Bid, Auction.id == Bid.auction_id
    ).filter(
        Auction.end_time <= datetime.utcnow(),
        Auction.end_time >= start_date,
        Bid.id.in_(
            db.session.query(func.max(Bid.id)).group_by(Bid.auction_id)
        )
    ).group_by(User.username).order_by(func.count(Auction.id).desc()).limit(10).all()
    
    # Top sellers (by earnings)
    top_sellers_by_earnings = db.session.query(
        User.username,
        func.sum(Bid.amount).label('earnings')
    ).join(
        Auction, User.id == Auction.seller_id
    ).join(
        Bid, Auction.id == Bid.auction_id
    ).filter(
        Auction.end_time <= datetime.utcnow(),
        Auction.end_time >= start_date,
        Bid.id.in_(
            db.session.query(func.max(Bid.id)).group_by(Bid.auction_id)
        )
    ).group_by(User.username).order_by(func.sum(Bid.amount).desc()).limit(10).all()
    
    # Most active bidders (by number of bids)
    top_bidders = db.session.query(
        User.username,
        func.count(Bid.id).label('bid_count')
    ).join(
        Bid, User.id == Bid.bidder_id
    ).filter(
        Bid.created_at >= start_date
    ).group_by(User.username).order_by(func.count(Bid.id).desc()).limit(10).all()
    
    # New user registrations over time
    new_users = db.session.query(
        func.count(User.id).label('user_count')
    ).filter(
        User.created_at >= start_date,
        User.role == 'user'
    ).scalar()
    
    return {
        'top_sellers_by_count': top_sellers_by_count,
        'top_sellers_by_earnings': top_sellers_by_earnings,
        'top_bidders': top_bidders,
        'new_users': new_users
    }