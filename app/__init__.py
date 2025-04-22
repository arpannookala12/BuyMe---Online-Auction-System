from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.item import item_bp
    from app.routes.auction import auction_bp
    from app.routes.search import search_bp
    from app.routes.alert import alert_bp
    from app.routes.customer_rep import customer_rep_bp
    from app.routes.admin import admin_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(item_bp)
    app.register_blueprint(auction_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(customer_rep_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    
    return app