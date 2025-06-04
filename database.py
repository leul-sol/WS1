from pymongo import MongoClient
from datetime import datetime
import logging
from config import Config
import certifi
import ssl

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """Initialize MongoDB connection."""
        try:
            if not Config.MONGODB_URI:
                raise ValueError("MONGODB_URI is not configured")
            if not Config.MONGODB_DATABASE:
                raise ValueError("MONGODB_DATABASE is not configured")
            if not Config.MONGODB_COLLECTION:
                raise ValueError("MONGODB_COLLECTION is not configured")

            # Add SSL/TLS settings to the connection
            self.client = MongoClient(
                Config.MONGODB_URI,
                tls=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000
            )
            
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[str(Config.MONGODB_DATABASE)]
            self.collection = self.db[str(Config.MONGODB_COLLECTION)]
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def insert_many(self, documents):
        """Insert multiple documents into the collection."""
        try:
            if not documents:
                logger.warning("No documents to insert")
                return None
                
            # Add timestamp to each document
            for doc in documents:
                doc['scraped_at'] = datetime.utcnow()
                
            result = self.collection.insert_many(documents)
            logger.info(f"Successfully inserted {len(result.inserted_ids)} documents")
            return result
        except Exception as e:
            logger.error(f"Failed to insert documents: {e}")
            raise

    def find_one(self, query):
        """Find a single document matching the query."""
        try:
            return self.collection.find_one(query)
        except Exception as e:
            logger.error(f"Failed to find document: {e}")
            raise

    def find_many(self, query):
        """Find multiple documents matching the query."""
        try:
            return list(self.collection.find(query))
        except Exception as e:
            logger.error(f"Failed to find documents: {e}")
            raise

    def update_one(self, query, update):
        """Update a single document matching the query."""
        try:
            result = self.collection.update_one(query, update)
            logger.info(f"Modified {result.modified_count} document(s)")
            return result
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            raise

    def delete_one(self, query):
        """Delete a single document matching the query."""
        try:
            result = self.collection.delete_one(query)
            logger.info(f"Deleted {result.deleted_count} document(s)")
            return result
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise

    def close(self):
        """Close the MongoDB connection."""
        try:
            if hasattr(self, 'client'):
                self.client.close()
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Failed to close MongoDB connection: {e}")
            raise