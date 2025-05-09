import logging
from config import Config
from database import Database
from scraper import TwitterScraper
import time

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=Config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler()
        ]
    )

def main():
    """Main function to run the Twitter scraper"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database
        database = Database()
        
        # Initialize scraper
        scraper = TwitterScraper(database)
        
        # Login to Twitter
        if scraper.login():
            time.sleep(3)  # Wait for login to complete
            
            # Navigate to profile
            if scraper.go_to_profile():
                time.sleep(3)  # Wait for profile to load
                
                # Start scraping
                scraper.scrape_posts()
                
                # Keep browser open to view results
                time.sleep(Config.VIEW_RESULTS_TIME)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        # Clean up
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main() 