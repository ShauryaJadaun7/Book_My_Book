# BookMyBook

A college-only book sharing marketplace (buy, borrow, barter).

## Features
- OTP-based registration
- College email domain restriction
- Buy books using upi qr code
- Borrow books with star rating approval and automated late fees
- Barter books with specific/general preferences
- Rating system

## Setup
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install requirements: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill the variables.
6. Run migrations: `flask db upgrade`
7. Run development server: `flask run`

## Running Celery
`celery -A tasks.celery_app.celery worker --loglevel=info`
`celery -A tasks.celery_app.celery beat --loglevel=info`
