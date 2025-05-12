from pymongo import MongoClient
from datetime import datetime
import logging
from config import Config
import certifi
import ssl

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.setup_connection()

    def setup_connection(self):
        """Initialize MongoDB connection"""
        try:
            if not Config.MONGODB_URI:
                raise ValueError("MONGODB_URI not found in environment variables")

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
            
            self.db = self.client[Config.MONGODB_DATABASE]
            self.collection = self.db[Config.MONGODB_COLLECTION]
            
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise

    def save_tweet(self, tweet_data):
        """Save or update a tweet in the database"""
        try:
            # Add timestamp for when the data was scraped
            tweet_data['scraped_at'] = datetime.utcnow()
            
            # Check if tweet already exists
            existing_tweet = self.collection.find_one({
                'timestamp': tweet_data['timestamp'],
                'text': tweet_data['text']
            })
            
            if existing_tweet:
                # Update existing tweet
                self.collection.update_one(
                    {'_id': existing_tweet['_id']},
                    {'$set': {
                        'metrics': tweet_data['metrics'],
                        'updated_at': datetime.utcnow()
                    }}
                )
                logger.info(f"Updated existing tweet from {tweet_data['timestamp']}")
            else:
                # Insert new tweet
                self.collection.insert_one(tweet_data)
                logger.info(f"Inserted new tweet from {tweet_data['timestamp']}")
                
            return True
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {str(e)}")
            return False

    def get_tweets(self, query=None, limit=0):
        """Retrieve tweets from the database"""
        try:
            if query is None:
                query = {}
            return list(self.collection.find(query).limit(limit))
        except Exception as e:
            logger.error(f"Error retrieving tweets: {str(e)}")
            return []

    def close(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed") 