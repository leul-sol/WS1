import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Twitter credentials
    TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
    TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
    
    # MongoDB settings
    MONGODB_URI = os.getenv('MONGODB_URI')
    MONGODB_DATABASE = 'twitter_scraper'
    MONGODB_COLLECTION = 'tweets'
    
    # Scraping settings
    MAX_POSTS = 50
    SCROLL_PAUSE_TIME = 2
    BROWSER_WAIT_TIME = 10
    VIEW_RESULTS_TIME = 30
    
    # Chrome options
    CHROME_OPTIONS = [
        '--start-maximized',
        # '--headless',  # Uncomment to run in headless mode
    ]
    
    # Logging settings
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'twitter_scraper.log' 