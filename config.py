import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
SADCAPTCHA_API_KEY = os.getenv('SADCAPTCHA_API_KEY')

# Scraping Settings
MAX_RESULTS_PER_KEYWORD = 30
MAX_COMMENTS_PER_VIDEO = 50
SCROLL_TIMEOUT = 2000  # milliseconds
PAGE_LOAD_TIMEOUT = 60000  # milliseconds
SEARCH_TIMEOUT = 30000  # milliseconds

# Browser Settings
BROWSER_VIEWPORT = {
    'width': 1280,
    'height': 720
}

# File Paths
USER_DATA_DIR = os.path.join(os.getcwd(), "playwright_user_data")
LOG_FILE = 'tiktok_scraper.log'
KEYWORDS_FILE = 'keywords.txt'

# Output Settings
OUTPUT_DIR = 'results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_output_file(keyword):
    """Generate output filename for a keyword."""
    safe_keyword = "".join(c if c.isalnum() else "_" for c in keyword)
    return os.path.join(OUTPUT_DIR, f"tiktok_search_results_{safe_keyword}.json")

class Config:
    # MongoDB settings
    MONGODB_URI = str(os.getenv('MONGODB_URI', ''))
    MONGODB_DATABASE = str(os.getenv('MONGODB_DATABASE', 'tiktok_scraper'))
    MONGODB_COLLECTION = str(os.getenv('MONGODB_COLLECTION', 'new_posts_comment'))