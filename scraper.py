from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import json
import logging
import time
from config import Config
import os

logger = logging.getLogger(__name__)

class TwitterScraper:
    def __init__(self, database):
        self.database = database
        self.driver = None
        self.wait = None
        self.posts = []
        self.setup_browser()

    def setup_browser(self):
        """Initialize the Chrome browser"""
        try:
            chrome_options = Options()
            for option in Config.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # Use local ChromeDriver
            service = Service("chromedriver.exe")  # Make sure chromedriver.exe is in your project directory
            
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            self.wait = WebDriverWait(self.driver, Config.BROWSER_WAIT_TIME)
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}")
            # Clean up any partial initialization
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            raise

    def login(self):
        """Login to Twitter"""
        try:
            self.driver.get('https://twitter.com/login')
            time.sleep(3)  # Wait for page to load

            # Enter username
            username_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            username_input.send_keys(Config.TWITTER_USERNAME)
            
            # Click next button
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
            )
            next_button.click()

            # Enter password
            password_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.send_keys(Config.TWITTER_PASSWORD)

            # Click login button
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
            )
            login_button.click()

            logger.info("Successfully logged in to Twitter")
            return True

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False

    def go_to_profile(self):
        """Navigate to user profile"""
        try:
            profile_link = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/webper_1'][aria-label='Profile']"))
            )
            profile_link.click()
            logger.info("Successfully navigated to profile")
            return True
        except Exception as e:
            logger.error(f"Error navigating to profile: {str(e)}")
            return False

    def extract_tweet_data(self, article):
        """Extract data from a tweet article"""
        try:
            # Get tweet text
            tweet_text_element = article.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
            tweet_text = tweet_text_element.text
            
            # Get timestamp
            time_element = article.find_element(By.TAG_NAME, 'time')
            timestamp = time_element.get_attribute('datetime')
            
            # Get username and handle
            username_element = article.find_element(By.CSS_SELECTOR, 'div[data-testid="User-Name"]')
            username = username_element.find_element(By.CSS_SELECTOR, 'div[dir="ltr"] span').text
            handle = username_element.find_element(By.CSS_SELECTOR, 'div[dir="ltr"] span[class*="r-1ttztb7"]').text
            
            # Get engagement metrics
            metrics = {}
            for metric in ['reply', 'retweet', 'like']:
                try:
                    metric_element = article.find_element(By.CSS_SELECTOR, f'div[data-testid="{metric}"]')
                    metric_text = metric_element.find_element(By.CSS_SELECTOR, 'span[class*="r-1ttztb7"]').text
                    metrics[metric] = metric_text if metric_text else '0'
                except:
                    metrics[metric] = '0'
            
            # Get views if available
            try:
                views_element = article.find_element(By.CSS_SELECTOR, 'a[href*="/analytics"]')
                views = views_element.find_element(By.CSS_SELECTOR, 'span[class*="r-1ttztb7"]').text
                metrics['views'] = views
            except:
                metrics['views'] = '0'
            
            # Get hashtags
            hashtags = []
            try:
                hashtag_elements = tweet_text_element.find_elements(By.CSS_SELECTOR, 'a[href*="hashtag"]')
                hashtags = [tag.text for tag in hashtag_elements]
            except:
                pass
            
            return {
                'text': tweet_text,
                'timestamp': timestamp,
                'username': username,
                'handle': handle,
                'metrics': metrics,
                'hashtags': hashtags
            }
        except Exception as e:
            logger.error(f"Error extracting tweet data: {str(e)}")
            return None

    def scrape_posts(self):
        """Scrape tweets from the profile"""
        try:
            logger.info("Starting to scrape posts...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while len(self.posts) < Config.MAX_POSTS:
                tweet_articles = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
                
                for article in tweet_articles:
                    if len(self.posts) >= Config.MAX_POSTS:
                        break
                    
                    tweet_data = self.extract_tweet_data(article)
                    if tweet_data:
                        # Save to database
                        self.database.save_tweet(tweet_data)
                        
                        # Add to posts list if not already present
                        if tweet_data not in self.posts:
                            self.posts.append(tweet_data)
                            logger.info(f"Scraped post {len(self.posts)} of {Config.MAX_POSTS}")
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(Config.SCROLL_PAUSE_TIME)
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("Reached the end of the page")
                    break
                last_height = new_height
            
            # Save posts to JSON file as backup
            self.save_posts_to_json()
            return True
            
        except Exception as e:
            logger.error(f"Error during post scraping: {str(e)}")
            return False

    def save_posts_to_json(self):
        """Save scraped posts to a JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"twitter_posts_{timestamp}.json"
            
            # Convert posts to JSON-serializable format
            serializable_posts = []
            for post in self.posts:
                post_copy = post.copy()
                # Convert ObjectId to string if present
                if '_id' in post_copy:
                    post_copy['_id'] = str(post_copy['_id'])
                if 'scraped_at' in post_copy:
                    post_copy['scraped_at'] = post_copy['scraped_at'].isoformat()
                if 'updated_at' in post_copy:
                    post_copy['updated_at'] = post_copy['updated_at'].isoformat()
                serializable_posts.append(post_copy)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_posts, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Successfully saved {len(self.posts)} posts to {filename}")
        except Exception as e:
            logger.error(f"Error saving posts to JSON: {str(e)}")

    def close(self):
        """Close the browser and database connection"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
        if self.database:
            self.database.close() 