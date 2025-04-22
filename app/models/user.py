from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # Increase the size of the password_hash column from 128 to at least 256
    password_hash = db.Column(db.String(256), nullable=False)  # Changed from 128 to 256
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    address = db.Column(db.String(256))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user')  # 'user', 'customer_rep', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    auctions = db.relationship('Auction', backref='seller', lazy='dynamic')
    bids = db.relationship('Bid', backref='bidder', lazy='dynamic')
    alerts = db.relationship('Alert', backref='user', lazy='dynamic')
    
    def __init__(self, username, email, password, **kwargs):
        super(User, self).__init__(**kwargs)
        self.username = username
        self.email = email
        self.set_password(password)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_customer_rep(self):
        return self.role == 'customer_rep'

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))