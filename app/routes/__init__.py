from flask import Blueprint

# Create blueprints for different sections of the application
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
user_bp = Blueprint('user', __name__, url_prefix='/user')
item_bp = Blueprint('item', __name__, url_prefix='/item')
auction_bp = Blueprint('auction', __name__, url_prefix='/auction')
search_bp = Blueprint('search', __name__, url_prefix='/search')
alert_bp = Blueprint('alert', __name__, url_prefix='/alert')
customer_rep_bp = Blueprint('customer_rep', __name__, url_prefix='/rep')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
main_bp = Blueprint('main', __name__)
review_bp = Blueprint('review',__name__,url_prefix='/review')
wishlist_bp = Blueprint('wishlist', __name__, url_prefix='/wishlist')
api_bp = Blueprint('api', __name__, url_prefix='/api')
notification_bp = Blueprint('notification', __name__, url_prefix='/notification')
# Don't import routes here to avoid circular imports
# Instead, import blueprints in the app/__init__.py file after creating them

# Export blueprints for registration with app
__all__ = [
    'auth_bp', 'user_bp', 'item_bp', 'auction_bp', 'search_bp', 
    'alert_bp', 'customer_rep_bp', 'admin_bp', 'main_bp','review_bp','wishlist_bp','api_bp','notification_bp'
]