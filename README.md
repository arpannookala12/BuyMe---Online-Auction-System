# BuyMe - Online Auction System

BuyMe is a comprehensive online auction platform inspired by eBay, built as part of CS 527 - Database Systems project. The system allows users to buy and sell items through online auctions with a rich feature set and intuitive user experience.

## Features Implemented

### User Management
- ✅ Create accounts (buyers, sellers)
- ✅ Login and logout functionality
- ✅ User profile management
- ✅ User roles: Regular users, Customer Representatives, and Administrators

### Auction Management
- ✅ Sellers can create auctions and post items for sale
- ✅ Set all item characteristics including images
- ✅ Set closing date and time for auctions
- ✅ Set hidden minimum price (reserve)
- ✅ Hierarchical category system with attributes

### Bidding System
- ✅ Manual bidding on items
- ✅ Automatic bidding with secret upper limits and bid increments
- ✅ Notifications when outbid
- ✅ Alerts when bids exceed upper limits
- ✅ Winner determination at auction close
- ✅ Winner notifications

### Browse and Search
- ✅ Browse items by category and various criteria
- ✅ Advanced search with multiple filters
- ✅ View bid history for any auction
- ✅ View all auctions a specific user has participated in
- ✅ View similar items from recent auctions

### Alert System
- ✅ Set alerts for specific items of interest
- ✅ Receive notifications when matching items become available
- ✅ Email notifications (configurable)

### Q&A System
- ✅ Users can post questions to customer representatives
- ✅ Browse and search questions and answers
- ✅ Customer representatives can respond to inquiries

### Customer Representative Functions
- ✅ Answer user questions
- ✅ Edit/delete account information
- ✅ Remove bids when necessary
- ✅ Remove auctions that violate policies

### Administrative Functions
- ✅ Create accounts for customer representatives
- ✅ Generate comprehensive sales reports including:
  - Total earnings
  - Earnings per item
  - Earnings per item type
  - Earnings per end-user
  - Best-selling items
  - Best buyers
- ✅ Monitor system performance and activity

### Additional Features
- ✅ Wishlist functionality
- ✅ Real-time notifications with Socket.IO
- ✅ User reviews and ratings
- ✅ Automated auction closing and winner determination
- ✅ Mobile-responsive design

## Technology Stack

- **Frontend**: HTML, CSS, Bootstrap, JavaScript
- **Backend**: Flask (Python)
- **Database**: MySQL with SQLAlchemy ORM
- **Real-time Communication**: Socket.IO
- **Task Scheduling**: APScheduler
- **Email**: Flask-Mail

## Database Schema

![Database ER Diagram](image.png)

Our database schema includes the following main entities:

- **Users**: End users, customer representatives, and administrators
- **Items**: Products being sold with detailed attributes
- **Categories**: Hierarchical category system with custom attributes
- **Auctions**: Listings with bidding information and status
- **Bids**: Individual bids placed on auctions
- **Alerts**: User-defined criteria for item notifications
- **Questions/Answers**: Support system communications
- **Notifications**: System notifications for various events
- **Wishlists**: User-saved items of interest
- **Reviews**: User feedback and ratings

## Setup Instructions

### Prerequisites

- Python 3.7+
- MySQL Server

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/BuyMe---Online-Auction-System.git
   cd BuyMe---Online-Auction-System
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root with the following content:
   ```
   SECRET_KEY=your-secret-key
   DATABASE_URL=mysql+mysqlconnector://username:password@localhost/buyme
   
   # Mail settings (optional)
   MAIL_SERVER=smtp.example.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   MAIL_DEFAULT_SENDER=your-email@example.com
   ```
   Replace placeholders with your actual credentials.

5. **Create the database**:
   ```bash
   mysql -u root -p
   ```
   ```sql
   CREATE DATABASE buyme;
   ```

6. **Initialize the database**:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

7. **Create an admin user**:
   ```bash
   python create_admin.py
   ```
   Follow the prompts to create your admin account.

8. **Populate the database with sample data** (optional):
   ```bash
   python seed_data.py
   ```

9. **Run the application**:
   ```bash
   python run.py
   ```

10. **Access the application** at `http://localhost:5001`

## User Roles and Access

### Regular Users
- Can register for accounts through the registration page
- Can buy and sell items through auctions
- Can set alerts for items of interest
- Can place bids and use automatic bidding
- Can add items to wishlist and leave reviews
- Can ask questions to customer representatives

### Customer Representatives
- Created by administrators
- Can answer user questions
- Can edit user information
- Can remove bids and auctions
- Can manage system content

### Administrators
- Initial admin account created using `create_admin.py`
- Can create customer representatives
- Can generate sales reports
- Can manage categories and system settings
- Can monitor all system activity

## Contributors

- Ganesh Arpan Nookala (gn178)
- Ronit Gandhi (rg1225)
- Prerna Nookala (kn491)

## License

This project is licensed under the MIT License - see the LICENSE file for details.