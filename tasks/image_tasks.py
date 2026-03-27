import os
import sys
import redis
from celery import shared_task
from flask import current_app

# Add parent directory to path to import run module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run import app

@shared_task
def persist_cover_image(filename):
    """
    Fetch the image binary from Redis and save to the persistent disk storage.
    """
    with app.app_context():
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/1')
        redis_client = redis.from_url(redis_url)
        
        redis_key = f"cover_image:{filename}"
        image_data = redis_client.get(redis_key)
        
        if image_data:
            upload_path = os.path.join(current_app.root_path, 'static', 'covers')
            os.makedirs(upload_path, exist_ok=True)
            picture_path = os.path.join(upload_path, filename)
            
            with open(picture_path, 'wb') as f:
                f.write(image_data)
                
            print(f"Successfully persisted image {filename} to disk.")
        else:
            print(f"Image data for {filename} not found in Redis. It might have expired or already been persisted.")
