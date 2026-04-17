import os
from celery import Celery
from celery.schedules import crontab

def make_celery(app_name="book_my_book"):
    # Priority: Looks for 'REDIS_URL', then 'CELERY_BROKER_URL', then local fallback
    redis_url = os.environ.get('REDIS_URL') or \
                os.environ.get('CELERY_BROKER_URL') or \
                'redis://localhost:6379/0'
    
    celery_instance = Celery(
        app_name,
        backend=redis_url,
        broker=redis_url,
        include=[
            'tasks.borrow_tasks', 
            'tasks.notification_tasks', 
            'tasks.image_tasks', 
            'tasks.listing_tasks'
        ]
    )

    # CRITICAL: SSL configuration for Upstash (rediss://)
    if redis_url.startswith('rediss://'):
        celery_instance.conf.update(
            broker_use_ssl={'ssl_cert_reqs': 'none'},
            redis_backend_use_ssl={'ssl_cert_reqs': 'none'},
            # Use 'redis' instead of 'rediss' in result_backend_transport_options if needed
            redis_backend_health_check_interval=30
        )

    # Modern Celery 5.0+ Configuration naming
    celery_instance.conf.update(
        timezone='UTC',
        enable_utc=True,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json'
    )

    return celery_instance

celery = make_celery()

# Periodic Task Schedule (The "Business Logic" Engine)
celery.conf.beat_schedule = {
    'check-overdue-books-every-day': {
        'task': 'tasks.borrow_tasks.check_overdue_books',
        'schedule': crontab(hour=0, minute=0),
    },
    'expire-unlisted-books-every-3-hours': {
        'task': 'tasks.listing_tasks.expire_old_listings',
        'schedule': crontab(minute=0, hour='*/3'),
    },
}
