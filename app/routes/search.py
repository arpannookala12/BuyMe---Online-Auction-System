from flask import Blueprint, render_template, request, jsonify
from app.models import Auction, Item, Category
from datetime import datetime
from sqlalchemy import or_, and_

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
def index():
    query = request.args.get('q', '')
    if not query:
        return render_template('search/index.html', results=None, query=None)
    
    # Search for auctions matching the query
    results = basic_search(query)
    
    return render_template('search/index.html', results=results, query=query)

@search_bp.route('/advanced')
def advanced():
    # Get all categories for the form
    categories = Category.query.filter_by(parent_id=None).all()
    
    # Check if this is a form submission
    if len(request.args) > 0:
        results = advanced_search(request.args)
        return render_template('search/advanced.html', categories=categories, results=results)
    
    return render_template('search/advanced.html', categories=categories, results=None)

@search_bp.route('/api/suggestions')
def suggestions():
    """API endpoint for search suggestions"""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    # Get auction titles matching the query
    current_time = datetime.utcnow()
    auctions = Auction.query.filter(
        Auction.is_active == True,
        Auction.end_time > current_time,
        Auction.title.ilike(f'%{query}%')
    ).limit(5).all()
    
    # Get item names matching the query
    items = Item.query.filter(
        Item.name.ilike(f'%{query}%')
    ).distinct(Item.name).limit(5).all()
    
    # Combine results
    suggestions = []
    for auction in auctions:
        if auction.title not in suggestions:
            suggestions.append(auction.title)
    
    for item in items:
        if item.name not in suggestions and len(suggestions) < 10:
            suggestions.append(item.name)
    
    return jsonify(suggestions)

def basic_search(query):
    """Perform a basic search on auctions and items"""
    current_time = datetime.utcnow()
    
    # Split query into terms
    terms = query.split()
    
    # Create search conditions
    conditions = []
    for term in terms:
        term_filter = or_(
            Auction.title.ilike(f'%{term}%'),
            Auction.description.ilike(f'%{term}%'),
            Item.name.ilike(f'%{term}%'),
            Item.description.ilike(f'%{term}%')
        )
        conditions.append(term_filter)
    
    # Get active auctions matching the query
    results = Auction.query.join(Item).filter(
        and_(*conditions),
        Auction.is_active == True,
        Auction.end_time > current_time
    ).order_by(Auction.end_time.asc()).all()
    
    return results

def advanced_search(args):
    """Perform an advanced search based on form parameters"""
    current_time = datetime.utcnow()
    
    # Extract search parameters
    query = args.get('query', '').strip()
    category_id = args.get('category_id', type=int)
    min_price = args.get('min_price', type=float)
    max_price = args.get('max_price', type=float)
    status = args.get('status', 'active')
    sort_by = args.get('sort', 'end_time_asc')
    
    # Start with base query
    search_query = Auction.query.join(Item)
    
    # Apply text search if provided
    if query:
        # Split query into terms
        terms = query.split()
        
        # Create search conditions
        conditions = []
        for term in terms:
            term_filter = or_(
                Auction.title.ilike(f'%{term}%'),
                Auction.description.ilike(f'%{term}%'),
                Item.name.ilike(f'%{term}%'),
                Item.description.ilike(f'%{term}%')
            )
            conditions.append(term_filter)
        
        search_query = search_query.filter(and_(*conditions))
    
    # Apply category filter if provided
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
        search_query = search_query.filter(Item.category_id.in_(category_ids))
    
    # Apply price filters if provided
    if min_price is not None:
        search_query = search_query.filter(Auction.initial_price >= min_price)
    
    if max_price is not None:
        search_query = search_query.filter(Auction.initial_price <= max_price)
    
    # Apply status filter
    if status == 'active':
        search_query = search_query.filter(
            Auction.is_active == True,
            Auction.end_time > current_time
        )
    elif status == 'ended':
        search_query = search_query.filter(Auction.end_time <= current_time)
    # 'all' doesn't need additional filtering
    
    # Apply sorting
    if sort_by == 'end_time_asc':
        search_query = search_query.order_by(Auction.end_time.asc())
    elif sort_by == 'end_time_desc':
        search_query = search_query.order_by(Auction.end_time.desc())
    elif sort_by == 'price_asc':
        search_query = search_query.order_by(Auction.initial_price.asc())
    elif sort_by == 'price_desc':
        search_query = search_query.order_by(Auction.initial_price.desc())
    elif sort_by == 'newest':
        search_query = search_query.order_by(Auction.created_at.desc())
    
    # Execute query
    results = search_query.all()
    
    return results