import logging
from scraper import TiktokScraper
from config import (
    LOG_FILE,
    KEYWORDS_FILE,
    MAX_RESULTS_PER_KEYWORD,
    MAX_COMMENTS_PER_VIDEO,
    get_output_file
)

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

def read_keywords(filename=KEYWORDS_FILE):
    """Read keywords from a file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # Read lines and strip whitespace, filter out empty lines
            keywords = [line.strip() for line in f.readlines() if line.strip()]
        return keywords
    except Exception as e:
        logging.error(f"Error reading keywords file: {e}")
        return []

def main():
    """Main function to run the TikTok scraper"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize scraper
        scraper = TiktokScraper()
        scraper.setup_browser()
        
        # Read keywords from file
        keywords = read_keywords()
        if not keywords:
            logger.error(f"No keywords found in {KEYWORDS_FILE}")
            return
            
        # Process each keyword
        for keyword in keywords:
            try:
                logger.info(f"Processing keyword: {keyword}")
                
                # Search for the keyword
                if not scraper.search_tiktok(keyword):
                    logger.error(f"Failed to search for keyword: {keyword}")
                    continue
                
                # Get output filename from config
                output_file = get_output_file(keyword)
                
                # Scrape results and comments
                scraper.scroll_and_scrape(
                    max_results=MAX_RESULTS_PER_KEYWORD,
                    max_comments_per_video=MAX_COMMENTS_PER_VIDEO,
                    output_file=output_file
                )
                
                logger.info(f"Completed processing keyword: {keyword}")
                
            except Exception as e:
                logger.error(f"Error processing keyword '{keyword}': {e}")
                continue
                
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main()
