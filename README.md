📚 BookMyBook

A Flask-powered platform for buying, borrowing, and bartering books

BookMyBook is a full-stack web application built using Flask that enables users to share books in a flexible and community-driven way. Instead of just buying books, users can borrow them for a period or barter by exchanging books — making reading more accessible and sustainable.

This project focuses on authentication, relational database design, and real-world transaction workflows, similar to marketplace platforms.

🚀 Key Features
🔐 User Authentication

Secure user registration and login

Password hashing using Werkzeug

Session management with Flask-Login

📘 Book Management

Upload books with:

Title

Author

Description

Cover image

Manage uploaded books from a personalized dashboard

🔄 Multiple Transaction Modes

BookMyBook supports three acquisition methods:

🛒 Buy

Users can directly purchase books at a fixed price set by the owner

📖 Borrow

Request books for a specific duration

Owners define borrowing fees and conditions

🔁 Barter

Propose book exchanges

Upload an image of the offered book

Owner can accept or reject the barter request

🔍 Dynamic Search

Real-time search on the homepage

Filter books by title or author

📊 User Dashboard

“My Books” section to:

Manage uploads

View incoming requests

Track transaction status

🛠 Tech Stack
Layer	Technology
Backend	Python, Flask
Database	PostgreSQL
ORM	SQLAlchemy
Migrations	Flask-Migrate
Frontend	HTML5, CSS3, JavaScript
Authentication	Flask-Login
Security	Werkzeug Password Hashing
⚙️ Installation & Setup
✅ Prerequisites

Python 3.12+

PostgreSQL

Git

📥 Step 1: Clone the Repository
git clone <repository-url>
cd BookMyBook

🧪 Step 2: Set Up Virtual Environment
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

📦 Step 3: Install Dependencies
pip install flask flask-sqlalchemy flask-login flask-migrate psycopg2-binary werkzeug

🔧 Step 4: Configure Database

Update the database URI in website/__init__.py:

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://username:password@localhost:5432/BookMyBook"


Make sure the database BookMyBook exists in PostgreSQL.

🗄 Step 5: Initialize the Database
set FLASK_APP=main.py     # Windows
export FLASK_APP=main.py # macOS/Linux

flask db init
flask db migrate -m "Initial migration"
flask db upgrade

▶️ Step 6: Run the Application
python main.py


Visit: http://127.0.0.1:5000

📁 Project Structure
BookMyBook/
│
├── website/
│   ├── auth.py        # Authentication routes
│   ├── models.py     # Database models
│   ├── routes.py     # Book and transaction routes
│   └── __init__.py   # App configuration
│
├── static/
│   ├── uploads/       # Book images
│   └── css/
│
├── templates/         # HTML templates
│
├── main.py            # Application entry point
└── README.md
