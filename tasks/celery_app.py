import os
from celery import Celery

def make_celery(app_name=__name__):
    broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    return Celery(
        app_name,
        backend=result_backend,
        broker=broker_url,
        include=['tasks.borrow_tasks', 'tasks.notification_tasks', 'tasks.image_tasks']
    )

celery = make_celery()

# Setup periodic tasks
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'check-overdue-books-every-day': {
        'task': 'tasks.borrow_tasks.check_overdue_books',
        'schedule': crontab(hour=0, minute=0), # Midnight daily
    },
}
celery.conf.timezone = 'UTC'
