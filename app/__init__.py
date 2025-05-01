from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_apscheduler import APScheduler
from config import Config
import json

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO()
scheduler = APScheduler()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)
    
    # Only initialize scheduler if it's not already running
    if not scheduler.running:
        scheduler.init_app(app)
        scheduler.start()
    
    # Add custom Jinja2 filter
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.auction import auction_bp
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp
    from app.routes.notification import notification_bp
    from app.routes.main import main_bp
    from app.routes.customer_rep import customer_rep_bp
    from app.routes.search import search_bp
    from app.routes.alert import alert_bp
    from app.routes.wishlist import wishlist_bp
    from app.routes.review import review_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(auction_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(customer_rep_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(review_bp)
    
    # Start background monitor
    from app.socket_events import start_background_monitor
    start_background_monitor(app)
    
    return app