from app import create_app, db
from app.models import User
import getpass

def create_admin_user():
    """Create an admin user for the BuyMe application"""
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(role='admin').first()
        if admin:
            print(f"Admin user already exists: {admin.username}")
            return
        
        print("Creating admin user...")
        
        # Get admin information
        username = input("Enter admin username: ")
        email = input("Enter admin email: ")
        password = getpass.getpass("Enter admin password: ")
        confirm_password = getpass.getpass("Confirm admin password: ")
        
        # Validate input
        if not username or not email or not password:
            print("All fields are required.")
            return
        
        if password != confirm_password:
            print("Passwords do not match.")
            return
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            print("Username already exists.")
            return
        
        if User.query.filter_by(email=email).first():
            print("Email already exists.")
            return
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            password=password,
            role='admin'
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{username}' created successfully!")

if __name__ == "__main__":
    create_admin_user()