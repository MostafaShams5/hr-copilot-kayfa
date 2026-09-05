"""MongoDB service for database operations."""

import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.config import settings

logger = logging.getLogger(__name__)

class MongoDBService:
    """MongoDB connection and database management."""
    
    _client = None
    _db = None
    
    @classmethod
    def connect(cls):
        """Connect to MongoDB Atlas."""
        try:
            if cls._client is None:
                cls._client = MongoClient(
                    settings.MONGODB_URI,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                )
                # Test connection
                cls._client.admin.command('ping')
                cls._db = cls._client[settings.MONGODB_DB_NAME]
                logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")
            return cls._db
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    @classmethod
    def get_db(cls):
        """Get database instance."""
        if cls._db is None:
            cls.connect()
        return cls._db
    
    @classmethod
    def disconnect(cls):
        """Disconnect from MongoDB."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("Disconnected from MongoDB")

# Initialize on import
db = MongoDBService.get_db()