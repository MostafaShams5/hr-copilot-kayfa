"""MongoDB Service"""

from pymongo import MongoClient
from datetime import datetime
from .config import settings

def get_db():
    """Get MongoDB connection"""
    client = MongoClient(settings.MONGODB_URI)
    return client[settings.MONGODB_DB_NAME]

def save_to_mongodb(screening_data):
    """Save screening result to MongoDB"""
    try:
        db = get_db()
        collection = db["cv_screenings"]
        
        screening_data["created_at"] = datetime.utcnow()
        result = collection.insert_one(screening_data)
        
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")
        return None