import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive 'Agg'
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Auction, Bid, Category, Item, CategoryAttribute, Review
from sqlalchemy import func
from functools import wraps
import csv
import pandas as pd
from flask import send_file
import json
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Custom decorator to check if the user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get basic statistics
    user_count = User.query.filter_by(is_admin=False, is_customer_rep=False).count()
    rep_count = User.query.filter_by(is_customer_rep=True).count()
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
    customer_reps = User.query.filter_by(is_customer_rep=True).order_by(User.username).all()
    
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
            is_customer_rep=True
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
        User.is_admin == False,
        User.is_customer_rep == False
    ).scalar()
    
    return {
        'top_sellers_by_count': top_sellers_by_count,
        'top_sellers_by_earnings': top_sellers_by_earnings,
        'top_bidders': top_bidders,
        'new_users': new_users
    }

@admin_bp.route('/category/<int:category_id>/attributes')
@login_required
@admin_required
def manage_category_attributes(category_id):
    """Manage attributes for a specific category"""
    category = Category.query.get_or_404(category_id)
    attributes = CategoryAttribute.query.filter_by(category_id=category_id).all()
    
    return render_template('admin/category_attributes.html', category=category, attributes=attributes)

@admin_bp.route('/category/<int:category_id>/attributes/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category_attribute(category_id):
    """Create a new attribute for a category"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        attribute_type = request.form.get('attribute_type')
        required = request.form.get('required') == 'on'
        options = request.form.get('options')
        
        # Validate input
        if not all([name, display_name, attribute_type]):
            flash('Name, Display Name, and Type are required', 'danger')
            return render_template('admin/create_category_attribute.html', category=category)
        
        # Create attribute
        attribute = CategoryAttribute(
            category_id=category_id,
            name=name,
            display_name=display_name,
            attribute_type=attribute_type,
            required=required,
            options=options
        )
        
        db.session.add(attribute)
        db.session.commit()
        
        flash('Category attribute created successfully', 'success')
        return redirect(url_for('admin.manage_category_attributes', category_id=category_id))
    
    return render_template('admin/create_category_attribute.html', category=category)

@admin_bp.route('/category/attribute/<int:attribute_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category_attribute(attribute_id):
    """Edit a category attribute"""
    attribute = CategoryAttribute.query.get_or_404(attribute_id)
    
    if request.method == 'POST':
        attribute.name = request.form.get('name')
        attribute.display_name = request.form.get('display_name')
        attribute.attribute_type = request.form.get('attribute_type')
        attribute.required = request.form.get('required') == 'on'
        attribute.options = request.form.get('options')
        
        db.session.commit()
        
        flash('Category attribute updated successfully', 'success')
        return redirect(url_for('admin.manage_category_attributes', category_id=attribute.category_id))
    
    return render_template('admin/edit_category_attribute.html', attribute=attribute)

@admin_bp.route('/category/attribute/<int:attribute_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category_attribute(attribute_id):
    """Delete a category attribute"""
    attribute = CategoryAttribute.query.get_or_404(attribute_id)
    category_id = attribute.category_id
    
    db.session.delete(attribute)
    db.session.commit()
    
    flash('Category attribute deleted successfully', 'success')
    return redirect(url_for('admin.manage_category_attributes', category_id=category_id))

@admin_bp.route('/reports/download/<report_type>/<period>/<format>')
@login_required
@admin_required
def download_report(report_type, period, format):
    """Generate downloadable report"""
    # Set time range based on period
    now = datetime.utcnow()
    if period == 'week':
        start_date = now - timedelta(days=7)
        period_name = "Last 7 Days"
    elif period == 'month':
        start_date = now - timedelta(days=30)
        period_name = "Last 30 Days"
    elif period == 'year':
        start_date = now - timedelta(days=365)
        period_name = "Last Year"
    else:  # all time
        start_date = datetime.min
        period_name = "All Time"
    
    # Generate report data based on type
    if report_type == 'earnings':
        report_data = generate_earnings_report(start_date)
        title = f"Earnings Report - {period_name}"
    elif report_type == 'items':
        report_data = generate_items_report(start_date)
        title = f"Items Report - {period_name}"
    elif report_type == 'users':
        report_data = generate_users_report(start_date)
        title = f"Users Report - {period_name}"
    else:
        return jsonify({'error': 'Invalid report type'}), 400
    
    # Generate the appropriate format
    if format == 'excel':
        return generate_excel_report(report_type, report_data, title)
    elif format == 'csv':
        return generate_csv_report(report_type, report_data, title)
    elif format == 'json':
        return jsonify(report_data)
    elif format == 'chart':
        return generate_chart(report_type, report_data, title)
    else:
        return jsonify({'error': 'Invalid format'}), 400


def generate_excel_report(report_type, report_data, title):
    """Generate Excel report from data"""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    if report_type == 'earnings':
        # Total earnings sheet
        pd.DataFrame([{'Total Earnings': report_data['total_earnings']}]).to_excel(
            writer, sheet_name='Summary', index=False)
        
        # Category earnings sheet
        category_data = [{'Category': category, 'Earnings': earnings} 
                         for category, earnings in report_data['category_earnings'].items()]
        pd.DataFrame(category_data).to_excel(writer, sheet_name='By Category', index=False)
        
        # Seller earnings sheet
        seller_data = [{'Seller': seller, 'Earnings': earnings} 
                       for seller, earnings in report_data['seller_earnings'].items()]
        pd.DataFrame(seller_data).to_excel(writer, sheet_name='By Seller', index=False)
    
    elif report_type == 'items':
        # Best selling items
        best_items = [{'Item': item, 'Sales Count': count} 
                     for item, count in report_data['best_selling_items']]
        pd.DataFrame(best_items).to_excel(writer, sheet_name='Best Selling Items', index=False)
        
        # Best selling categories
        best_categories = [{'Category': category, 'Sales Count': count}
                            for category, count in report_data['best_selling_categories']]
        pd.DataFrame(best_categories).to_excel(writer, sheet_name='Best Categories', index=False)
        
        # Most valuable items
        valuable_items = [{'Item': item, 'Auction': title, 'Highest Bid': bid} 
                         for item, title, bid in report_data['most_valuable_items']]
        pd.DataFrame(valuable_items).to_excel(writer, sheet_name='Most Valuable Items', index=False)
    
    elif report_type == 'users':
        # Top sellers by count
        top_sellers_count = [{'Seller': seller, 'Auctions Completed': count} 
                            for seller, count in report_data['top_sellers_by_count']]
        pd.DataFrame(top_sellers_count).to_excel(writer, sheet_name='Top Sellers (Count)', index=False)
        
        # Top sellers by earnings
        top_sellers_earnings = [{'Seller': seller, 'Earnings': earnings} 
                               for seller, earnings in report_data['top_sellers_by_earnings']]
        pd.DataFrame(top_sellers_earnings).to_excel(writer, sheet_name='Top Sellers (Earnings)', index=False)
        
        # Most active bidders
        top_bidders = [{'Bidder': bidder, 'Number of Bids': count} 
                       for bidder, count in report_data['top_bidders']]
        pd.DataFrame(top_bidders).to_excel(writer, sheet_name='Most Active Bidders', index=False)
        
        # New users
        pd.DataFrame([{'New User Registrations': report_data['new_users']}]).to_excel(
            writer, sheet_name='New Registrations', index=False)
    
    writer.save()
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"{title.replace(' ', '_')}.xlsx"
    )

def generate_csv_report(report_type, report_data, title):
    """Generate CSV report from data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == 'earnings':
        # Write header and total earnings
        writer.writerow(['Total Earnings'])
        writer.writerow([f"${report_data['total_earnings']:.2f}"])
        
        # Write category earnings
        writer.writerow([])  # Empty row as separator
        writer.writerow(['Category', 'Earnings'])
        for category, earnings in report_data['category_earnings'].items():
            writer.writerow([category, f"${earnings:.2f}"])
        
        # Write seller earnings
        writer.writerow([])  # Empty row as separator
        writer.writerow(['Seller', 'Earnings'])
        for seller, earnings in report_data['seller_earnings'].items():
            writer.writerow([seller, f"${earnings:.2f}"])
    
    elif report_type == 'items':
        # Write best selling items
        writer.writerow(['Best Selling Items'])
        writer.writerow(['Item', 'Sales Count'])
        for item, count in report_data['best_selling_items']:
            writer.writerow([item, count])
        
        # Write best selling categories
        writer.writerow([])  # Empty row as separator
        writer.writerow(['Best Selling Categories'])
        writer.writerow(['Category', 'Sales Count'])
        for category, count in report_data['best_selling_categories']:
            writer.writerow([category, count])
        
        # Write most valuable items
        writer.writerow([])  # Empty row as separator
        writer.writerow(['Most Valuable Items'])
        writer.writerow(['Item', 'Auction', 'Highest Bid'])
        for item, title, bid in report_data['most_valuable_items']:
            writer.writerow([item, title, f"${bid:.2f}"])
    
    elif report_type == 'users':
        # Write top sellers by count
        writer.writerow(['Top Sellers by Auction Count'])
        writer.writerow(['Seller', 'Auctions Completed'])
        for seller, count in report_data['top_sellers_by_count']:
            writer.writerow([seller, count])
        
        # Write top sellers by earnings
        writer.writerow([])  # Empty row as separator
        writer.writerow(['Top Sellers by Earnings'])
        writer.writerow(['Seller', 'Earnings'])
        for seller, earnings in report_data['top_sellers_by_earnings']:
            writer.writerow([seller, f"${earnings:.2f}"])
        
        # Write most active bidders
        writer.writerow([])  # Empty row as separator
        writer.writerow(['Most Active Bidders'])
        writer.writerow(['Bidder', 'Number of Bids'])
        for bidder, count in report_data['top_bidders']:
            writer.writerow([bidder, count])
        
        # Write new users
        writer.writerow([])  # Empty row as separator
        writer.writerow(['New User Registrations'])
        writer.writerow([report_data['new_users']])
    
    output_string = output.getvalue()
    output_bytes = io.BytesIO(output_string.encode('utf-8'))
    output_bytes.seek(0)
    
    return send_file(
        output_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{title.replace(' ', '_')}.csv"
    )

def generate_chart(report_type, report_data, title):
    """Generate chart image from report data"""
    plt.figure(figsize=(10, 6))
    
    if report_type == 'earnings':
        # Category earnings pie chart
        categories = list(report_data['category_earnings'].keys())
        values = list(report_data['category_earnings'].values())
        
        plt.title(f"Earnings by Category - {title}")
        plt.pie(values, labels=categories, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    
    elif report_type == 'items':
        # Best selling items bar chart
        items = [item for item, _ in report_data['best_selling_items']]
        counts = [count for _, count in report_data['best_selling_items']]
        
        # Limit to top 10 for readability
        if len(items) > 10:
            items = items[:10]
            counts = counts[:10]
        
        plt.title(f"Best Selling Items - {title}")
        plt.barh(items, counts)
        plt.xlabel('Sales Count')
        plt.ylabel('Item')
        plt.tight_layout()
    
    elif report_type == 'users':
        # Top sellers by earnings bar chart
        sellers = [seller for seller, _ in report_data['top_sellers_by_earnings']]
        earnings = [earnings for _, earnings in report_data['top_sellers_by_earnings']]
        
        # Limit to top 10 for readability
        if len(sellers) > 10:
            sellers = sellers[:10]
            earnings = earnings[:10]
        
        plt.title(f"Top Sellers by Earnings - {title}")
        plt.barh(sellers, earnings)
        plt.xlabel('Earnings ($)')
        plt.ylabel('Seller')
        plt.tight_layout()
    
    # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('admin/user_details.html', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting admin accounts
    if user.is_admin:
        flash('Cannot delete admin accounts.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # Delete user's data
    Auction.query.filter_by(seller_id=user_id).delete()
    Bid.query.filter_by(bidder_id=user_id).delete()
    Review.query.filter_by(reviewer_id=user_id).delete()
    Review.query.filter_by(seller_id=user_id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/auctions/<int:auction_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_auction(auction_id):
    auction = Auction.query.get_or_404(auction_id)
    
    # Prevent deleting auctions from admin users
    if auction.seller.is_admin:
        flash('Cannot delete auctions from admin users.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    db.session.delete(auction)
    db.session.commit()
    
    flash('Auction deleted successfully.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/bids/<int:bid_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_bid(bid_id):
    bid = Bid.query.get_or_404(bid_id)
    
    # Prevent deleting bids from admin users
    if bid.bidder.is_admin:
        flash('Cannot delete bids from admin users.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    db.session.delete(bid)
    db.session.commit()
    
    flash('Bid deleted successfully.', 'success')
    return redirect(url_for('admin.manage_users'))