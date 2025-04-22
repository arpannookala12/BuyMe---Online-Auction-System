# BuyMe Auction System

BuyMe is an eBay-like online auction system built with Flask and MySQL that allows users to buy and sell items through online auctions. This project is developed as part of CS 527 - Database Systems.

## Features

### End Users (Buyers and Sellers)
- Account creation, login, and profile management
- Create auctions with item descriptions and photos
- Browse and search for items by various criteria
- Place bids on auctions with automatic bidding support
- Create alerts for items of interest
- View bid history and auction details
- Track personal bidding and selling activity

### Customer Representatives
- Assist users with account management
- Answer questions and resolve issues
- Modify user information when necessary
- Remove bids or illegal auctions
- Maintain system integrity

### Administrative Staff
- Create accounts for customer representatives
- Generate comprehensive sales reports
- Manage system categories
- Monitor overall system performance

## Technology Stack

- **Frontend**: HTML, CSS, Bootstrap
- **Backend**: Flask (Python)
- **Database**: MySQL with SQLAlchemy ORM
- **Web Server**: Local development server

## Project Structure

The project follows a modular structure:

```
buyme/
│
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── config.py            # Configuration settings
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py          # User, CustomerRep, Admin models
│   │   ├── item.py          # Item and category models
│   │   ├── auction.py       # Auction and bid models
│   │   └── alert.py         # Alert model
│   │
│   ├── routes/              # Route handlers
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication routes
│   │   ├── user.py          # User profile routes
│   │   ├── item.py          # Item management routes
│   │   ├── auction.py       # Auction and bidding routes
│   │   ├── search.py        # Search functionality
│   │   ├── alert.py         # Alert management
│   │   ├── customer_rep.py  # Customer representative routes
│   │   └── admin.py         # Admin routes
│   │
│   ├── static/              # Static files (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   │
│   └── templates/           # Jinja2 templates
│       ├── base.html        # Base template
│       ├── auth/            # Authentication templates
│       ├── user/            # User profile templates
│       ├── item/            # Item templates
│       ├── auction/         # Auction templates
│       ├── search/          # Search templates
│       ├── customer_rep/    # Customer representative templates
│       └── admin/           # Admin templates
│
├── migrations/              # Database migrations
│
├── tests/                   # Unit and integration tests
│
├── .env                     # Environment variables (not in git)
├── .gitignore               # Git ignore file
├── requirements.txt         # Project dependencies
├── run.py                   # Application entry point
├── create_admin.py          # Script to create admin user
├── seed_data.py             # Script to populate database with sample data
└── README.md                # Project documentation
```

## Database Schema

![Database ER Diagram](image.png)

The system is built around the following database entities:

- **Users**: End users, customer representatives, and administrators
- **Items**: Products being sold
- **Categories**: Hierarchical categories for organizing items
- **Auctions**: Listings with bidding information
- **Bids**: Individual bids placed on auctions
- **Alerts**: User-defined criteria for item notifications

## Setup Instructions

### Prerequisites

- Python 3.7+
- MySQL Server

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/buyme.git
   cd buyme
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
   ```
   Replace `username`, `password` with your MySQL credentials.

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

10. **Access the application** at `http://localhost:5000`

## User Roles and Access

The system has three types of users, each with different capabilities:

### Regular Users
- Created through the registration page
- Can buy and sell items
- Manage their own profile, auctions, and bids

### Customer Representatives
- Created by administrators
- Access the customer representative dashboard
- Help users with account issues
- Can deactivate auctions and remove bids

### Administrators
- Initial admin account created using `create_admin.py`
- Additional admins can be created through MySQL directly
- Access to the admin dashboard
- Can create customer representatives
- Generate reports and manage system settings

## Development Workflow

### Git Workflow

1. **Main branch**: Production-ready code
2. **Development branch**: Integration branch for features
3. **Feature branches**: Individual features or components

### Branch Naming Convention

- Feature branches: `feature/feature-name`
- Bug fixes: `fix/bug-name`
- Documentation: `docs/description`

### Creating a New Feature

1. Create a new branch from development:
   ```bash
   git checkout development
   git pull
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

3. Push your branch:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Create a Pull Request to the development branch

### Code Style

- Follow PEP 8
- Use docstrings for functions and classes
- Organize imports alphabetically
- Use clear variable and function names

## Testing

To run the test suite:

```bash
python -m pytest
```

## Contributors

- Ganesh Arpan Nookala (gn178)
- Ronit Gandhi
- Prerna Nookala (kn491)

## License

This project is licensed under the MIT LICENSE - see the LICENSE file for details.

## Acknowledgments

- Based on the CS 527 - Database Systems for Data Science course project requirements
- Inspired by eBay's auction system