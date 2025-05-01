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
        Bid.query.delete()
        Alert.query.delete()
        Auction.query.delete()
        Item.query.delete()
        Category.query.delete()
        
        # Keep admin users, delete regular users
        User.query.filter_by(is_admin=False, is_customer_rep=False).delete()
        
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
        
        # Combined items list - initial specialized items
        items_data = []
        items_data.extend(laptop_items)
        items_data.extend(smartphone_items)
        items_data.extend(headphone_items)
        items_data.extend(tv_items)
        items_data.extend(console_items)
        items_data.extend(smartwatch_items)
        
        # Add generic image URLs for different categories to be used for bulk items
        image_urls = {
            laptops.id: [
                "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1531297484001-80022131f5a1?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1596003906949-67221c37965c?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            ],
            smartphones.id: [
                "https://images.unsplash.com/photo-1598327105666-5b89351aff97?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1580910051074-3eb694886505?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            ],
            headphones.id: [
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            ],
            speakers.id: [
                "https://images.unsplash.com/photo-1545454675-3531b543be5d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            ],
            tvs.id: [
                "https://images.unsplash.com/photo-1601944179066-29786cb9d32a?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1461151304267-38535e780c79?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            ],
            consoles.id: [
                "https://images.unsplash.com/photo-1486572788966-cfd3df1f5b42?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1605901309584-818e25960a8f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            ],
            games.id: [
                "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1518908336710-4e1cf821d3d1?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            ],
            smartwatches.id: [
                "https://images.unsplash.com/photo-1546868871-7041f2a55e12?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
                "https://images.unsplash.com/photo-1617043786394-f977fa12eddf?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
            ]
        }
        
        # Default image for categories without specific images
        default_images = [
            "https://images.unsplash.com/photo-1550009158-9ebf69173e03?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1550745165-9bc0b252726f?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80",
            "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1000&q=80"
        ]
        
        # Add more items to reach 100+ with images
        category_ids = [
            laptops.id, desktops.id, tablets.id, components.id,
            smartphones.id, feature_phones.id, phone_accessories.id,
            headphones.id, speakers.id, home_audio.id,
            tvs.id, monitors.id, projectors.id,
            consoles.id, games.id, accessories.id,
            smartwatches.id, fitness_trackers.id, smart_glasses.id
        ]
        
        # Item names and descriptions by category
        item_templates = {
            laptops.id: [
                {"name": "Gaming Laptop", "desc": "High-performance gaming laptop with dedicated GPU"},
                {"name": "Ultrabook", "desc": "Thin and light laptop for productivity"},
                {"name": "Chromebook", "desc": "Affordable laptop running Chrome OS"},
                {"name": "2-in-1 Convertible", "desc": "Laptop that converts to tablet mode"}
            ],
            smartphones.id: [
                {"name": "Flagship Phone", "desc": "Premium smartphone with top specifications"},
                {"name": "Mid-range Phone", "desc": "Balanced performance and features at a reasonable price"},
                {"name": "Budget Phone", "desc": "Affordable smartphone with essential features"},
                {"name": "Camera Phone", "desc": "Smartphone with exceptional camera capabilities"}
            ],
            headphones.id: [
                {"name": "Noise-Cancelling Headphones", "desc": "Over-ear headphones with active noise cancellation"},
                {"name": "Wireless Earbuds", "desc": "True wireless earbuds with charging case"},
                {"name": "Gaming Headset", "desc": "Headphones with microphone for gaming"},
                {"name": "Studio Headphones", "desc": "Professional-grade headphones for audio production"}
            ]
        }
        
        # Brand names by category
        brands = {
            laptops.id: ["Dell", "HP", "Lenovo", "ASUS", "Acer", "MSI", "Razer", "Microsoft"],
            desktops.id: ["Dell", "HP", "Lenovo", "ASUS", "Acer", "CyberPower", "iBuyPower", "Apple"],
            tablets.id: ["Apple", "Samsung", "Microsoft", "Lenovo", "Amazon", "Huawei"],
            components.id: ["NVIDIA", "AMD", "Intel", "Corsair", "ASUS", "MSI", "Western Digital", "Samsung"],
            smartphones.id: ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi", "Motorola", "Sony", "Nothing"],
            headphones.id: ["Sony", "Bose", "Sennheiser", "Apple", "JBL", "Audio-Technica", "Beyerdynamic", "Beats"],
            speakers.id: ["Sonos", "Bose", "JBL", "UE", "Anker", "Marshall", "Harman Kardon"],
            tvs.id: ["Samsung", "LG", "Sony", "TCL", "Hisense", "Vizio", "Panasonic"]
        }
        
        # Generate bulk items for each category to reach 100+ total
        for i in range(1, 80):  # Adjust number as needed to reach 100+ with the specialized items
            # Select a random category
            category_id = random.choice(category_ids)
            
            # Select or generate a name and description
            if category_id in item_templates:
                template = random.choice(item_templates[category_id])
                name = f"{random.choice(brands.get(category_id, ['Brand']))} {template['name']} Model {i}"
                description = f"{template['desc']} - Edition {i}"
            else:
                name = f"Electronics Item {i}"
                description = f"High-quality electronic device with advanced features #{i}"
            
            # Select an image URL
            if category_id in image_urls and image_urls[category_id]:
                image_url = random.choice(image_urls[category_id])
            else:
                image_url = random.choice(default_images)
            
            # Generate some attributes based on category
            attributes = "quality:High"
            
            if category_id == laptops.id:
                attributes += f",brand:{random.choice(brands[laptops.id])},processor:{random.choice(['Intel i5', 'Intel i7', 'AMD Ryzen 5', 'AMD Ryzen 7'])},ram:{random.choice(['8GB', '16GB', '32GB'])},storage:{random.choice(['256GB', '512GB', '1TB'])}"
            elif category_id == smartphones.id:
                attributes += f",brand:{random.choice(brands[smartphones.id])},storage:{random.choice(['64GB', '128GB', '256GB'])},camera:{random.choice(['12MP', '48MP', '64MP'])}"
            elif category_id == headphones.id:
                attributes += f",brand:{random.choice(brands[headphones.id])},type:{random.choice(['Over-ear', 'In-ear', 'On-ear'])},wireless:{random.choice(['Yes', 'No'])}"
            
            # Create the item
            item_data = {
                "name": name,
                "description": description,
                "category_id": category_id,
                "attributes": attributes,
                "image_url": image_url
            }
            
            items_data.append(item_data)
        
        # Create items
        print(f"Creating {len(items_data)} total items...")
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
        
        # Create auctions - one auction per item
        print("Creating auctions...")
        now = datetime.utcnow()
        auctions = []
        
        for i, item in enumerate(items):
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
                end_time=end_time
            )
            auctions.append(auction)
            db.session.add(auction)
        
        db.session.flush()  # Flush to get auction IDs
        
        # Create bids - more realistic bid patterns
        print("Creating sample bids...")
        for auction in auctions:
            # Determine how popular this auction is (0-100%)
            popularity = random.random()
            
            # Skip some auctions to have some without bids
            if popularity < 0.15:  # 15% of auctions get no bids
                continue
                
            # Popular items get more bids
            if popularity > 0.9:  # Top 10% most popular items
                num_bids = random.randint(8, 15)
            elif popularity > 0.7:  # Next 20% 
                num_bids = random.randint(5, 8)
            elif popularity > 0.4:  # Middle 30%
                num_bids = random.randint(3, 5)
            else:  # Bottom 25% that get bids
                num_bids = random.randint(1, 3)
            
            current_price = auction.initial_price
            
            # Create bidding history with realistic time patterns
            bid_times = []
            auction_duration = (auction.end_time - now).total_seconds()
            
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
                
                bid_time = now + timedelta(seconds=time_offset)
                bid_times.append(bid_time)
            
            # Sort bid times chronologically
            bid_times.sort()
            
            # Create the bids with increasing amounts
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
                    is_auto_bid=False,
                    auto_bid_limit=auto_bid_limit
                )
                db.session.add(bid)
                
                current_price = bid_amount
        
        # Create alerts for users interested in electronics
        print("Creating sample alerts...")
        # Electronics keywords by category
        electronics_keywords = {
            'laptops': ['laptop', 'macbook', 'dell xps', 'gaming laptop', 'ultrabook'],
            'smartphones': ['iphone', 'samsung galaxy', 'pixel', 'android', 'smartphone'],
            'audio': ['headphones', 'earbuds', 'speaker', 'soundbar', 'wireless audio'],
            'gaming': ['playstation', 'xbox', 'nintendo switch', 'gaming console', 'controller'],
            'wearables': ['smartwatch', 'fitness tracker', 'apple watch', 'garmin'],
            'tvs': ['oled tv', '4k tv', 'smart tv', 'qled', 'home theater']
        }
        
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
        
        # Create customer rep if none exists
        customer_reps = User.query.filter_by(is_customer_rep=True).all()
        if not customer_reps:
            rep = User(
                username="customer_rep",
                email="customer_rep@buyme.com",
                is_customer_rep=True
            )
            rep.set_password("customer123")
            db.session.add(rep)
            db.session.commit()
            customer_reps = [rep]

        # Create sample questions and answers for the Q&A system
        print("Creating sample questions and answers...")
        
        # Sample questions and answers
        question_templates = [
            {"question_text": "How do I cancel a bid?", "content": "I placed a bid by mistake and want to cancel it."},
            {"question_text": "What happens if the seller doesn't ship my item?", "content": "I won an auction but haven't received my item yet."},
            {"question_text": "How does automatic bidding work?", "content": "Can someone explain how the auto-bidding feature works?"},
            {"question_text": "Can I sell items without an auction?", "content": "Is there a way to sell items directly without bidding?"},
            {"question_text": "How do I report a fake listing?", "content": "I found a suspicious listing, what should I do?"},
            {"question_text": "What fees does BuyMe charge?", "content": "What are the fees for selling items on this platform?"},
            {"question_text": "How do I contact a seller?", "content": "I have questions about an item before bidding."},
            {"question_text": "Can I change my username?", "content": "I want to update my username, is it possible?"},
            {"question_text": "What payment methods are accepted?", "content": "Which payment methods can I use to pay for items?"},
            {"question_text": "How do I track my order?", "content": "Where can I find tracking information for my purchase?"}
        ]

        # More question templates for variety
        more_question_templates = [
            {"question_text": "How do I delete my account?", "content": "I want to close my account permanently."},
            {"question_text": "Can I sell internationally?", "content": "Can I list items for international buyers?"},
            {"question_text": "Why was my listing removed?", "content": "My auction was taken down without explanation."}
        ]

        question_templates.extend(more_question_templates)

        # Create questions and answers
        print("Creating sample questions and answers...")
        for auction in auctions[:20]:  # Only create Q&A for first 20 auctions
            # Create 1-3 questions per auction
            num_questions = random.randint(1, 3)
            for i in range(num_questions):
                template = random.choice(question_templates)
                asker = random.choice(users)
                
                question = Question(
                    user_id=asker.id,
                    auction_id=auction.id,
                    question_text=template["question_text"]
                )
                db.session.add(question)
                db.session.flush()

                # Create an answer from a customer rep
                answer_text = f"Thank you for your question. {template['content']}"
                answer = Answer(
                    question_id=question.id,
                    user_id=random.choice(customer_reps).id,
                    answer_text=answer_text
                )
                db.session.add(answer)
        
        # Commit all changes
        db.session.commit()
        
        print(f"Database seeded successfully with {len(items_data)} items, {len(auctions)} auctions!")

if __name__ == "__main__":
    seed_data()