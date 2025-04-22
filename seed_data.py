from app import create_app, db
from app.models import User, Category, Item, Auction, Bid, Alert
from datetime import datetime, timedelta
import random

def seed_data():
    """Seed the database with sample data"""
    app = create_app()
    
    with app.app_context():
        print("Seeding database with sample data...")
        
        # Clear existing data
        Bid.query.delete()
        Alert.query.delete()
        Auction.query.delete()
        Item.query.delete()
        Category.query.delete()
        
        # Keep admin users, delete regular users
        User.query.filter_by(role='user').delete()
        
        # Commit the deletions
        db.session.commit()
        
        # Create sample users
        print("Creating sample users...")
        users = []
        for i in range(1, 11):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="password123",
                first_name=f"First{i}",
                last_name=f"Last{i}",
                address=f"Address {i}, City, State, ZIP",
                phone=f"123-456-{7890+i}"
            )
            users.append(user)
            db.session.add(user)
        
        # Create sample categories (Electronics category with subcategories)
        print("Creating sample categories...")
        electronics = Category(name="Electronics", description="Electronic devices and gadgets")
        db.session.add(electronics)
        db.session.flush()  # Flush to get the ID
        
        # Create subcategories
        computers = Category(name="Computers", description="Desktop and laptop computers", parent_id=electronics.id)
        phones = Category(name="Phones", description="Mobile phones and smartphones", parent_id=electronics.id)
        audio = Category(name="Audio", description="Headphones, speakers, and audio equipment", parent_id=electronics.id)
        db.session.add_all([computers, phones, audio])
        db.session.flush()  # Flush to get IDs
        
        # Create sub-subcategories
        laptops = Category(name="Laptops", description="Portable computers", parent_id=computers.id)
        desktops = Category(name="Desktops", description="Desktop computers", parent_id=computers.id)
        tablets = Category(name="Tablets", description="Tablet computers", parent_id=computers.id)
        
        smartphones = Category(name="Smartphones", description="Smart mobile phones", parent_id=phones.id)
        feature_phones = Category(name="Feature Phones", description="Basic mobile phones", parent_id=phones.id)
        
        headphones = Category(name="Headphones", description="Over-ear and in-ear headphones", parent_id=audio.id)
        speakers = Category(name="Speakers", description="Audio speakers", parent_id=audio.id)
        
        db.session.add_all([laptops, desktops, tablets, smartphones, feature_phones, headphones, speakers])
        
        # Create a second main category
        clothing = Category(name="Clothing", description="Apparel and fashion items")
        db.session.add(clothing)
        db.session.flush()
        
        mens = Category(name="Men's", description="Men's clothing", parent_id=clothing.id)
        womens = Category(name="Women's", description="Women's clothing", parent_id=clothing.id)
        kids = Category(name="Kids", description="Children's clothing", parent_id=clothing.id)
        db.session.add_all([mens, womens, kids])
        db.session.flush()
        # Create sample items and auctions
        print("Creating sample items and auctions...")
        
        # Sample items for each category
        items_data = [
            # Laptops
            {
                "name": "MacBook Pro", 
                "description": "13-inch MacBook Pro with M1 chip", 
                "category_id": laptops.id,
                "attributes": "brand:Apple,color:Silver,screen_size:13 inches,processor:M1"
            },
            {
                "name": "Dell XPS", 
                "description": "15-inch Dell XPS with Intel i7", 
                "category_id": laptops.id,
                "attributes": "brand:Dell,color:Black,screen_size:15 inches,processor:Intel i7"
            },
            # Smartphones
            {
                "name": "iPhone 13", 
                "description": "Apple iPhone 13 with 128GB storage", 
                "category_id": smartphones.id,
                "attributes": "brand:Apple,color:Blue,storage:128GB,camera:12MP"
            },
            {
                "name": "Samsung Galaxy S21", 
                "description": "Samsung Galaxy S21 with 256GB storage", 
                "category_id": smartphones.id,
                "attributes": "brand:Samsung,color:Phantom Gray,storage:256GB,camera:64MP"
            },
            # Headphones
            {
                "name": "Sony WH-1000XM4", 
                "description": "Wireless noise-cancelling headphones", 
                "category_id": headphones.id,
                "attributes": "brand:Sony,color:Black,type:Over-ear,wireless:Yes"
            },
            {
                "name": "AirPods Pro", 
                "description": "Apple wireless earbuds with noise cancellation", 
                "category_id": headphones.id,
                "attributes": "brand:Apple,color:White,type:In-ear,wireless:Yes"
            },
            # Men's Clothing
            {
                "name": "Leather Jacket", 
                "description": "Men's black leather jacket", 
                "category_id": mens.id,
                "attributes": "material:Leather,color:Black,size:L,season:Winter"
            },
            {
                "name": "Cotton T-Shirt", 
                "description": "Men's white cotton t-shirt", 
                "category_id": mens.id,
                "attributes": "material:Cotton,color:White,size:M,season:Summer"
            },
            # Women's Clothing
            {
                "name": "Wool Coat", 
                "description": "Women's gray wool winter coat", 
                "category_id": womens.id,
                "attributes": "material:Wool,color:Gray,size:M,season:Winter"
            },
            {
                "name": "Summer Dress", 
                "description": "Women's floral summer dress", 
                "category_id": womens.id,
                "attributes": "material:Cotton,color:Floral,size:S,season:Summer"
            }
        ]
        
        # Create items
        items = []
        for item_data in items_data:
            item = Item(
                name=item_data["name"],
                description=item_data["description"],
                category_id=item_data["category_id"],
                attributes=item_data["attributes"]
            )
            items.append(item)
            db.session.add(item)
        
        db.session.flush()  # Flush to get item IDs
        
        # Create auctions
        now = datetime.utcnow()
        auctions = []
        
        for i, item in enumerate(items):
            # Randomize auction end times
            end_time = now + timedelta(days=random.randint(1, 14))
            
            # Assign a random seller
            seller = random.choice(users)
            
            auction = Auction(
                item_id=item.id,
                seller_id=seller.id,
                title=f"{item.name} for Sale",
                description=f"I'm selling my {item.name}. {item.description}",
                initial_price=random.randint(50, 500),
                min_increment=5.0,
                secret_min_price=random.randint(100, 1000),
                end_time=end_time
            )
            auctions.append(auction)
            db.session.add(auction)
        
        db.session.flush()  # Flush to get auction IDs
        
        # Create bids
        print("Creating sample bids...")
        for auction in auctions:
            # Skip some auctions to have some without bids
            if random.random() < 0.2:
                continue
                
            # Generate 1-5 bids per auction
            num_bids = random.randint(1, 5)
            current_price = auction.initial_price
            
            for _ in range(num_bids):
                # Select a random bidder (not the seller)
                potential_bidders = [u for u in users if u.id != auction.seller_id]
                if not potential_bidders:
                    continue
                    
                bidder = random.choice(potential_bidders)
                
                # Increase the bid amount
                bid_amount = current_price + auction.min_increment + random.randint(0, 50)
                
                # Sometimes add auto-bidding
                auto_bid_limit = None
                if random.random() < 0.3:
                    auto_bid_limit = bid_amount + random.randint(50, 200)
                
                bid = Bid(
                    auction_id=auction.id,
                    bidder_id=bidder.id,
                    amount=bid_amount,
                    auto_bid_limit=auto_bid_limit,
                    created_at=now - timedelta(hours=random.randint(1, 48))
                )
                db.session.add(bid)
                
                current_price = bid_amount
        
        # Create alerts
        print("Creating sample alerts...")
        for user in users:
            # Skip some users to have some without alerts
            if random.random() < 0.5:
                continue
                
            # Generate 1-3 alerts per user
            num_alerts = random.randint(1, 3)
            
            for _ in range(num_alerts):
                # Randomly choose what to include in the alert
                include_keywords = random.random() < 0.7
                include_category = random.random() < 0.5
                include_price = random.random() < 0.6
                
                keywords = None
                category_id = None
                min_price = None
                max_price = None
                
                if include_keywords:
                    keyword_options = ["laptop", "phone", "headphones", "jacket", "dress", 
                                     "apple", "samsung", "sony", "dell", "leather", "wool"]
                    keywords = ", ".join(random.sample(keyword_options, random.randint(1, 3)))
                
                if include_category:
                    category_options = [laptops.id, smartphones.id, headphones.id, 
                                       mens.id, womens.id]
                    category_id = random.choice(category_options)
                
                if include_price:
                    min_price = random.randint(50, 300) if random.random() < 0.5 else None
                    max_price = random.randint(300, 1000) if random.random() < 0.5 else None
                
                alert = Alert(
                    user_id=user.id,
                    keywords=keywords,
                    category_id=category_id,
                    min_price=min_price,
                    max_price=max_price,
                    is_active=True
                )
                db.session.add(alert)
        
        # Commit all changes
        db.session.commit()
        
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_data()