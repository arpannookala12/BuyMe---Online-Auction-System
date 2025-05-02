from app import create_app, db
from app.models import User, Category, Item, Auction, Bid, Alert
from app.models.question import Question, Answer
from datetime import datetime, timedelta
import random

def seed_data():
    """Seed the database with sample data for electronics with images"""
    app = create_app()
    
    with app.app_context():
        print("Seeding database with electronics sample data...")
        
        # Clear existing data
        Answer.query.delete()
        Question.query.delete()
        Bid.query.delete()
        Alert.query.delete()
        Auction.query.delete()
        Item.query.delete()
        Category.query.delete()
        
        # Keep admin users, delete regular users and customer reps
        User.query.filter_by(is_admin=False).delete()
        
        # Commit the deletions
        db.session.commit()
        
        # Create sample users
        print("Creating sample users...")
        users = []
        for i in range(1, 21):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com"
            )
            user.set_password("password123")
            users.append(user)
            db.session.add(user)
        
        # Create customer rep
        rep = User(
            username="customer_rep",
            email="customer_rep@buyme.com",
            is_customer_rep=True
        )
        rep.set_password("customer123")
        db.session.add(rep)
        
        # Create Electronics category with subcategories
        print("Creating electronics categories hierarchy...")
        electronics = Category(name="Electronics", description="Electronic devices and gadgets")
        db.session.add(electronics)
        db.session.flush()  # Flush to get the ID
        
        # Create main subcategories
        computers = Category(name="Computers", description="Desktop and laptop computers", parent_id=electronics.id)
        phones = Category(name="Phones", description="Mobile phones and smartphones", parent_id=electronics.id)
        audio = Category(name="Audio", description="Headphones, speakers, and audio equipment", parent_id=electronics.id)
        tv_video = Category(name="TV & Video", description="Televisions, monitors, and video equipment", parent_id=electronics.id)
        gaming = Category(name="Gaming", description="Gaming consoles and accessories", parent_id=electronics.id)
        wearables = Category(name="Wearables", description="Smartwatches and fitness trackers", parent_id=electronics.id)
        
        db.session.add_all([computers, phones, audio, tv_video, gaming, wearables])
        db.session.flush()  # Flush to get IDs
        
        # Create sub-subcategories
        # Computer subcategories
        laptops = Category(name="Laptops", description="Portable computers", parent_id=computers.id)
        desktops = Category(name="Desktops", description="Desktop computers", parent_id=computers.id)
        tablets = Category(name="Tablets", description="Tablet computers", parent_id=computers.id)
        components = Category(name="Components", description="Computer parts and components", parent_id=computers.id)
        
        # Phone subcategories
        smartphones = Category(name="Smartphones", description="Smart mobile phones", parent_id=phones.id)
        feature_phones = Category(name="Feature Phones", description="Basic mobile phones", parent_id=phones.id)
        phone_accessories = Category(name="Phone Accessories", description="Cases, chargers, and more", parent_id=phones.id)
        
        # Audio subcategories
        headphones = Category(name="Headphones", description="Over-ear and in-ear headphones", parent_id=audio.id)
        speakers = Category(name="Speakers", description="Audio speakers", parent_id=audio.id)
        home_audio = Category(name="Home Audio", description="Home theater and sound systems", parent_id=audio.id)
        
        # TV & Video subcategories
        tvs = Category(name="TVs", description="Televisions", parent_id=tv_video.id)
        monitors = Category(name="Monitors", description="Computer monitors", parent_id=tv_video.id)
        projectors = Category(name="Projectors", description="Video projectors", parent_id=tv_video.id)
        
        # Gaming subcategories
        consoles = Category(name="Consoles", description="Gaming consoles", parent_id=gaming.id)
        games = Category(name="Games", description="Video games", parent_id=gaming.id)
        accessories = Category(name="Gaming Accessories", description="Controllers, headsets, etc.", parent_id=gaming.id)
        
        # Wearables subcategories
        smartwatches = Category(name="Smartwatches", description="Smart wrist watches", parent_id=wearables.id)
        fitness_trackers = Category(name="Fitness Trackers", description="Activity and fitness monitors", parent_id=wearables.id)
        smart_glasses = Category(name="Smart Glasses", description="AR and smart glasses", parent_id=wearables.id)
        
        db.session.add_all([
            laptops, desktops, tablets, components,
            smartphones, feature_phones, phone_accessories,
            headphones, speakers, home_audio,
            tvs, monitors, projectors,
            consoles, games, accessories,
            smartwatches, fitness_trackers, smart_glasses
        ])
        
        db.session.flush()
        
        # Create sample items for each category with images
        print("Creating sample items and auctions...")
        
        # Laptop items
        laptop_items = [
            {
                "name": "MacBook Pro 16-inch", 
                "description": "16-inch MacBook Pro with M1 Max chip, 32GB RAM, 1TB SSD", 
                "category_id": laptops.id,
                "attributes": "brand:Apple,color:Space Gray,screen_size:16 inches,processor:M1 Max,ram:32GB,storage:1TB,year:2023",
                "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            },
            {
                "name": "MacBook Air", 
                "description": "13-inch MacBook Air with M2 chip, 8GB RAM, 512GB SSD", 
                "category_id": laptops.id,
                "attributes": "brand:Apple,color:Silver,screen_size:13 inches,processor:M2,ram:8GB,storage:512GB,year:2023",
                "image_url": "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            },
            {
                "name": "Dell XPS 15", 
                "description": "15-inch Dell XPS with Intel i9, 32GB RAM, 1TB SSD", 
                "category_id": laptops.id,
                "attributes": "brand:Dell,color:Silver,screen_size:15 inches,processor:Intel i9,ram:32GB,storage:1TB,year:2023",
                "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            }
        ]
        
        # Smartphone items
        smartphone_items = [
            {
                "name": "iPhone 15 Pro Max", 
                "description": "Apple iPhone 15 Pro Max with 1TB storage", 
                "category_id": smartphones.id,
                "attributes": "brand:Apple,storage:1TB,color:Titanium,camera:48MP,screen_size:6.7 inches,year:2023",
                "image_url": "https://images.unsplash.com/photo-1678685888221-cda773a3dcdb?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            },
            {
                "name": "Samsung Galaxy S23 Ultra", 
                "description": "Samsung flagship with 200MP camera, 512GB storage", 
                "category_id": smartphones.id,
                "attributes": "brand:Samsung,storage:512GB,color:Phantom Black,camera:200MP,screen_size:6.8 inches,year:2023",
                "image_url": "https://images.unsplash.com/photo-1678828556610-61270b233ec0?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            }
        ]
        
        # Headphone items
        headphone_items = [
            {
                "name": "Sony WH-1000XM5", 
                "description": "Wireless noise-cancelling headphones with 30-hour battery", 
                "category_id": headphones.id,
                "attributes": "brand:Sony,type:Over-ear,wireless:Yes,noise_cancelling:Yes,battery:30 hours,color:Black,year:2023",
                "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            },
            {
                "name": "Apple AirPods Pro 2", 
                "description": "Wireless earbuds with active noise cancellation", 
                "category_id": headphones.id,
                "attributes": "brand:Apple,type:In-ear,wireless:Yes,noise_cancelling:Yes,battery:6 hours,color:White,year:2022",
                "image_url": "https://images.unsplash.com/photo-1606741965509-304243f4b7c6?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            }
        ]
        
        # TV items
        tv_items = [
            {
                "name": "LG C2 65-inch OLED TV", 
                "description": "65-inch OLED 4K TV with perfect blacks and gaming features", 
                "category_id": tvs.id,
                "attributes": "brand:LG,screen_size:65 inches,resolution:4K,panel:OLED,refresh_rate:120Hz,year:2023",
                "image_url": "https://images.unsplash.com/photo-1593305841991-05c297ba4575?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            }
        ]
        
        # Gaming console items
        console_items = [
            {
                "name": "PlayStation 5", 
                "description": "Sony's latest gaming console with 1TB SSD", 
                "category_id": consoles.id,
                "attributes": "brand:Sony,model:PS5,storage:1TB,color:White,edition:Standard,year:2022",
                "image_url": "https://images.unsplash.com/photo-1607853202273-797f1c22a38e?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            },
            {
                "name": "Xbox Series X", 
                "description": "Microsoft's high-end gaming console", 
                "category_id": consoles.id,
                "attributes": "brand:Microsoft,model:Series X,storage:1TB,color:Black,year:2022",
                "image_url": "https://images.unsplash.com/photo-1621259182978-fbf93132d53d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            }
        ]
        
        # Smartwatch items
        smartwatch_items = [
            {
                "name": "Apple Watch Series 8", 
                "description": "Latest Apple Watch with advanced health features", 
                "category_id": smartwatches.id,
                "attributes": "brand:Apple,size:45mm,connectivity:GPS+Cellular,color:Midnight,material:Aluminum,year:2022",
                "image_url": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            }
        ]
        
        # Combine all item data
        items_data = laptop_items + smartphone_items + headphone_items + tv_items + console_items + smartwatch_items
        
        # Create Item objects
        items = []
        for item_data in items_data:
            item = Item(
                name=item_data["name"],
                description=item_data["description"],
                category_id=item_data["category_id"],
                attributes=item_data["attributes"],
                image_url=item_data["image_url"]
            )
            items.append(item)
            db.session.add(item)
        
        db.session.flush()  # Flush to get item IDs
        
        # Current time for auction creation
        now = datetime.utcnow()
        auctions = []
        
        # Create active auctions (40% of items)
        print("Creating active auctions...")
        active_items = items[:int(len(items) * 0.4)]
        for i, item in enumerate(active_items):
            # Randomize auction end times - from 1 to 14 days in the future
            end_time = now + timedelta(days=random.randint(1, 14))
            
            # Assign a random seller from the users list
            seller = random.choice(users)
            
            # Create a more realistic auction title
            if i % 4 == 0:
                title = f"Brand New {item.name} - Great Deal!"
            elif i % 4 == 1:
                title = f"{item.name} - Barely Used, Perfect Condition"
            elif i % 4 == 2:
                title = f"SALE: {item.name} - Limited Time Offer"
            else:
                title = f"{item.name} for Sale - Fast Shipping"
                
            # Create more detailed description
            description = f"I'm selling my {item.name}. {item.description}\n\n"
            description += "This item is in excellent condition and comes with all original packaging and accessories. "
            description += "Ships from a smoke-free, pet-free home within 1 business day of payment. "
            description += "Please feel free to ask any questions before bidding!"
            
            # Generate realistic pricing based on perceived value
            item_value_factor = random.uniform(0.5, 3.0)  # Some items worth more than others
            base_price = random.randint(50, 1000)
            initial_price = round(base_price * item_value_factor, 2)
            min_increment = round(initial_price * 0.05, 2)  # 5% of initial price
            secret_min_price = round(initial_price * 1.5, 2)  # 50% more than initial
            
            auction = Auction(
                item_id=item.id,
                seller_id=seller.id,
                title=title,
                description=description,
                initial_price=initial_price,
                min_increment=min_increment,
                secret_min_price=secret_min_price,
                end_time=end_time,
                is_active=True
            )
            auctions.append(auction)
            db.session.add(auction)
        
        # Create completed auctions (60% of items) - ended with winners
        print("Creating completed auctions with winners...")
        completed_items = items[int(len(items) * 0.4):]
        for i, item in enumerate(completed_items):
            # Auction ended 1-30 days ago
            end_time = now - timedelta(days=random.randint(1, 30))
            
            # Assign a random seller from the users list
            seller = random.choice(users)
            
            # Create a more realistic auction title
            if i % 4 == 0:
                title = f"[COMPLETED] Brand New {item.name}"
            elif i % 4 == 1:
                title = f"[SOLD] {item.name} - Barely Used"
            elif i % 4 == 2:
                title = f"[ENDED] {item.name} - Limited Time Offer"
            else:
                title = f"[COMPLETE] {item.name} - Fast Shipping"
                
            # Create more detailed description
            description = f"I'm selling my {item.name}. {item.description}\n\n"
            description += "This item is in excellent condition and comes with all original packaging and accessories. "
            description += "Ships from a smoke-free, pet-free home within 1 business day of payment. "
            description += "Please feel free to ask any questions before bidding!"
            
            # Generate realistic pricing based on perceived value
            item_value_factor = random.uniform(0.5, 3.0)
            base_price = random.randint(50, 1000)
            initial_price = round(base_price * item_value_factor, 2)
            min_increment = round(initial_price * 0.05, 2)
            secret_min_price = round(initial_price * 1.5, 2)
            
            auction = Auction(
                item_id=item.id,
                seller_id=seller.id,
                title=title,
                description=description,
                initial_price=initial_price,
                min_increment=min_increment,
                secret_min_price=secret_min_price,
                end_time=end_time,
                is_active=False
            )
            auctions.append(auction)
            db.session.add(auction)
        
        db.session.flush()  # Flush to get auction IDs
        
        # Create bids for all auctions
        print("Creating sample bids...")
        for auction in auctions:
            # Determine how popular this auction is (0-100%)
            popularity = random.random()
            
            # Skip some auctions to have some without bids (only 10% of active auctions)
            if auction.is_active and popularity < 0.1:
                continue
                
            # All completed auctions should have bids
            if auction.is_active:
                # Popular items get more bids
                if popularity > 0.9:  # Top 10% most popular items
                    num_bids = random.randint(8, 15)
                elif popularity > 0.7:  # Next 20% 
                    num_bids = random.randint(5, 8)
                elif popularity > 0.4:  # Middle 30%
                    num_bids = random.randint(3, 5)
                else:  # Bottom 40% that get bids
                    num_bids = random.randint(1, 3)
            else:
                # Completed auctions have more bids on average
                num_bids = random.randint(5, 15)
            
            current_price = auction.initial_price
            
            # Create bidding history with realistic time patterns
            bid_times = []
            if auction.is_active:
                auction_duration = (auction.end_time - now).total_seconds()
            else:
                # For completed auctions, bids are in the past
                auction_duration = (auction.end_time - (auction.end_time - timedelta(days=14))).total_seconds()
            
            for _ in range(num_bids):
                # Bids are more likely to happen near the beginning and end of auctions
                if random.random() < 0.3:
                    # Early bid - first 25% of auction time
                    time_offset = random.uniform(0, auction_duration * 0.25)
                elif random.random() < 0.6:
                    # Late bid - last 15% of auction time
                    time_offset = random.uniform(auction_duration * 0.85, auction_duration * 0.99)
                else:
                    # Middle bid
                    time_offset = random.uniform(auction_duration * 0.25, auction_duration * 0.85)
                
                if auction.is_active:
                    bid_time = now + timedelta(seconds=time_offset)
                else:
                    # For completed auctions, bids are in the past
                    bid_time = auction.end_time - timedelta(seconds=(auction_duration - time_offset))
                
                bid_times.append(bid_time)
            
            # Sort bid times chronologically
            bid_times.sort()
            
            # Create the bids with increasing amounts
            winning_bid = None
            winning_bidder = None
            
            for i, bid_time in enumerate(bid_times):
                # Select a random bidder (not the seller)
                potential_bidders = [u for u in users if u.id != auction.seller_id]
                if not potential_bidders:
                    continue
                    
                bidder = random.choice(potential_bidders)
                
                # First bid is usually just above the initial price
                if i == 0:
                    bid_amount = current_price + auction.min_increment + random.uniform(0, 10)
                else:
                    # Later bids increase more as people get competitive
                    # More aggressive bidding near the end
                    if i > len(bid_times) * 0.7:
                        bid_amount = current_price + auction.min_increment + random.uniform(5, 30)
                    else:
                        bid_amount = current_price + auction.min_increment + random.uniform(0, 15)
                
                bid_amount = round(bid_amount, 2)
                
                # Sometimes add auto-bidding
                auto_bid_limit = None
                if random.random() < 0.4:  # 40% chance of auto-bidding
                    # Auto-bid limit is typically 20-40% higher than the current bid
                    auto_bid_limit = round(bid_amount * (1 + random.uniform(0.2, 0.4)), 2)
                
                bid = Bid(
                    auction_id=auction.id,
                    bidder_id=bidder.id,
                    amount=bid_amount,
                    is_auto_bid=False if auto_bid_limit is None else True,
                    auto_bid_limit=auto_bid_limit
                )
                # Set created_at manually after creation if the model supports it
                if hasattr(bid, 'created_at'):
                    bid.created_at = bid_time
                db.session.add(bid)
                
                current_price = bid_amount
                winning_bid = bid
                winning_bidder = bidder
            
            # For completed auctions, set a winner
            if not auction.is_active and winning_bid:
                auction.winner_id = winning_bidder.id
                auction.winning_bid_id = winning_bid.id
        
        # Create alerts for users interested in electronics
        print("Creating sample alerts...")
        for user in users[:10]:  # Create alerts for first 10 users
            num_alerts = random.randint(1, 3)
            for _ in range(num_alerts):
                category = random.choice([laptops, smartphones, headphones, tvs, consoles, smartwatches])
                alert = Alert(
                    user_id=user.id,
                    category_id=category.id,
                    keywords=f"{random.choice(['new', 'used', 'mint'])} {random.choice(['Apple', 'Samsung', 'Sony', 'Dell'])}",
                    min_price=random.randint(100, 500),
                    max_price=random.randint(1000, 2000),
                    is_active=True
                )
                db.session.add(alert)
        
        # Create sample questions without answers for customer reps to answer later
        print("Creating sample questions (without answers)...")
        
        # Sample questions
        question_templates = [
            "How do I cancel a bid?",
            "What happens if the seller doesn't ship my item?",
            "How does automatic bidding work?",
            "Can I sell items without an auction?",
            "How do I report a fake listing?",
            "What fees does BuyMe charge?",
            "How do I contact a seller?",
            "Can I change my username?",
            "What payment methods are accepted?",
            "How do I track my order?",
            "How do I delete my account?",
            "Can I sell internationally?",
            "Why was my listing removed?",
            "How long do auctions typically last?",
            "Is there a mobile app I can use?",
            "Can I have multiple shipping addresses?",
            "How do I get a refund for damaged items?",
            "Are there bulk listing options for sellers?",
            "How do I filter search results by location?",
            "What happens if I win multiple auctions from the same seller?"
        ]

        # Create questions for some auctions
        for auction in auctions[:30]:  # Create questions for first 30 auctions
            # Create 1-3 questions per auction
            num_questions = random.randint(1, 3)
            for i in range(num_questions):
                asker = random.choice(users)
                
                question = Question(
                    user_id=asker.id,
                    auction_id=auction.id,
                    text=random.choice(question_templates),
                    created_at=now - timedelta(days=random.randint(0, 10))
                )
                db.session.add(question)
        
        # Commit all changes
        db.session.commit()
        
        print(f"Database seeded successfully with {len(items_data)} items, {len(auctions)} auctions!")

if __name__ == "__main__":
    seed_data() 