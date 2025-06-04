import json
import logging
import time
import urllib.parse
import os
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from tiktok_captcha_solver import make_playwright_solver_context
from config import (
    SADCAPTCHA_API_KEY,
    MAX_RESULTS_PER_KEYWORD,
    MAX_COMMENTS_PER_VIDEO,
    SCROLL_TIMEOUT,
    PAGE_LOAD_TIMEOUT,
    SEARCH_TIMEOUT,
    BROWSER_VIEWPORT,
    USER_DATA_DIR,
    Config
)

from database import Database

logger = logging.getLogger(__name__)

class TiktokScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.last_request_time = 0
        self.min_request_delay = 2
        self.max_request_delay = 5
        self.database = Database() if Config.MONGODB_URI else None

    def _print_debug_info(self, data_type, data):
        """Print debug information about scraped data."""
        logger.info(f"\n{'='*50}")
        logger.info(f"DEBUG: {data_type}")
        logger.info(f"{'='*50}")
        if isinstance(data, list):
            for idx, item in enumerate(data):
                logger.info(f"\nItem {idx + 1}:")
                for key, value in item.items():
                    logger.info(f"{key}: {value}")
        else:
            for key, value in data.items():
                logger.info(f"{key}: {value}")
        logger.info(f"{'='*50}\n")

    def _random_delay(self):
        """Add random delay between requests to avoid detection."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_delay:
            delay = random.uniform(self.min_request_delay, self.max_request_delay)
            logger.info(f"Adding delay of {delay:.2f} seconds")
            time.sleep(delay)
        
        self.last_request_time = time.time()

    def setup_browser(self):
        """Initialize Playwright browser and context with captcha solver."""
        logger.info("Setting up Playwright browser...")
        self.playwright = sync_playwright().start()
        
        logger.info(f"Using persistent user data directory: {USER_DATA_DIR}")

        try:
            self.context = make_playwright_solver_context(
                self.playwright,
                SADCAPTCHA_API_KEY,
                user_data_dir=USER_DATA_DIR,
                headless=False
            )
            logger.info("Playwright browser context with captcha solver initialized.")

            self.page = self.context.new_page()
            self.page.set_viewport_size(BROWSER_VIEWPORT)
            logger.info(f"Set viewport size to {BROWSER_VIEWPORT['width']}x{BROWSER_VIEWPORT['height']}")

        except Exception as e:
            logger.error(f"Error during Playwright setup with captcha solver: {e}")
            raise

    def search_tiktok(self, query):
        """Perform a search on TikTok using direct URL navigation."""
        logger.info(f"Searching TikTok for: {query}")
        try:
            self._random_delay()  # Add delay before search
            
            # URL encode the search query
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.tiktok.com/search?q={encoded_query}"
            
            # Navigate directly to the search URL
            self.page.goto(search_url, timeout=PAGE_LOAD_TIMEOUT)
            logger.info(f"Navigated to search URL: {search_url}")
            
            # Wait for search results to load
            self.page.wait_for_selector('div[data-e2e="search_top-item"]', timeout=SEARCH_TIMEOUT)
            self.page.wait_for_timeout(SCROLL_TIMEOUT)  # Additional wait for dynamic content
            
            logger.info("Search results loaded successfully")
            return True
                
        except PlaywrightTimeoutError:
            logger.error("Search results not found or not interactable within timeout.")
            self.page.screenshot(path="search_results_timeout.png")
            raise
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            self.page.screenshot(path="search_error.png")
            raise

    def scroll_and_scrape(self, max_results=MAX_RESULTS_PER_KEYWORD, max_comments_per_video=MAX_COMMENTS_PER_VIDEO, output_file="tiktok_search_results.json"):
        """Extract search results and their comments."""
        logger.info("Scraping search results and comments...")
        
        initial_results = []
        final_results = []
        
        try:
            # Wait for and get initial search results
            self.page.wait_for_selector('div[data-e2e="search_top-item"]', timeout=SEARCH_TIMEOUT)
            cards = self.page.query_selector_all('div[data-e2e="search_top-item"]')
            logger.info(f"Found {len(cards)} video cards on the first page of search results.")
            
            # Extract initial data from search results
            for index, card in enumerate(cards[:max_results]):
                try:
                    self._random_delay()  # Add delay between card processing
                    
                    video_url = ""
                    try:
                        a_tag = card.query_selector('a[href*="/video/"]')
                        if a_tag:
                            video_url = a_tag.get_attribute('href')
                    except Exception as e:
                        logger.warning(f"Failed to extract video URL from card {index}: {e}")

                    title = ""
                    try:
                        img_tag = card.query_selector('img[alt]')
                        if img_tag:
                            title = img_tag.get_attribute('alt').strip()
                    except Exception as e:
                        logger.warning(f"Failed to extract title from card {index}: {e}")

                    like = ""
                    try:
                        views_elem = card.query_selector('strong[data-e2e="video-views"]')
                        if views_elem:
                            like = views_elem.inner_text().strip()
                    except Exception as e:
                        logger.warning(f"Failed to extract likes from card {index}: {e}")

                    # Extract hashtags from the title
                    hashtags = []
                    if title:
                        words = title.split()
                        for word in words:
                            cleaned_word = word.rstrip('.,!?;:"\'') 
                            if cleaned_word.startswith('#') and len(cleaned_word) > 1:
                                hashtags.append(cleaned_word)
                                 
                    if video_url:
                        initial_results.append({
                            "title": title,
                            "video_url": video_url,
                            "like": like,
                            "comment": "",
                            "share": "",
                            "date": "",
                            "username": "",
                            "comments": [],
                            "hashtags": hashtags
                        })
                        logger.info(f"Extracted initial data for card {index}: {video_url}")

                except Exception as card_e:
                    logger.error(f"Error extracting initial data from card {index}: {card_e}")

            # Process each video to get comments and additional details
            for index, video_data in enumerate(initial_results):
                video_url = video_data["video_url"]
                logger.info(f"Processing video {index + 1}/{len(initial_results)}: {video_url}")

                try:
                    self._random_delay()
                    
                    # Navigate to video page
                    self.page.goto(video_url, timeout=PAGE_LOAD_TIMEOUT)
                    self.page.wait_for_load_state('domcontentloaded', timeout=SEARCH_TIMEOUT)
                    self.page.wait_for_timeout(SCROLL_TIMEOUT)

                    # Handle potential captcha/popup
                    try:
                        dialog_selector = 'div[role="dialog"][data-e2e="login-modal"]'
                        skip_button_selector = 'button.TUXButton--secondary:has-text("Skip")'
                        self.page.wait_for_selector(dialog_selector, state='visible', timeout=SEARCH_TIMEOUT)
                        self.page.wait_for_timeout(15000)
                        self.page.wait_for_selector(f'{dialog_selector} >> {skip_button_selector}', state='visible', timeout=10000)
                        self.page.click(f'{dialog_selector} >> {skip_button_selector}')
                    except PlaywrightTimeoutError:
                        logger.info("No popup/captcha detected")

                    # Extract video details with updated selectors
                    try:
                        # Username
                        user_elem = self.page.query_selector('span[data-e2e="browse-username"]')
                        if user_elem:
                            video_data["username"] = '@' + user_elem.inner_text().strip().lstrip('@')

                        # Date
                        date_elem = self.page.query_selector('span[data-e2e="browser-nickname"]')
                        if date_elem:
                            nickname_text = date_elem.inner_text().strip()
                            if '·' in nickname_text:
                                video_data["date"] = nickname_text.split('·')[-1].strip()

                        # Comment count
                        comment_elem = self.page.query_selector('strong[data-e2e="comment-count"]')
                        if comment_elem:
                            video_data["comment"] = comment_elem.inner_text().strip()

                        # Share count
                        share_elem = self.page.query_selector('strong[data-e2e="share-count"]')
                        if share_elem:
                            video_data["share"] = share_elem.inner_text().strip()

                    except Exception as e:
                        logger.warning(f"Failed to extract video details: {e}")

                    # Extract comments with updated selectors
                    comments = self.scrape_comments_from_page(max_comments_per_video)
                    video_data["comments"] = comments
                    logger.info(f"Scraped {len(comments)} comments for video {index + 1}")

                    # Print debug info for the video
                    self._print_debug_info("Video Data", video_data)

                    final_results.append(video_data)
                            
                except Exception as detail_e:
                    logger.error(f"Error processing video {video_url}: {detail_e}")
                    continue

            # Save results to JSON
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(final_results, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(final_results)} search results with comments to {output_file}")

            # Save to database if configured
            if self.database:
                try:
                    self.database.insert_many(final_results)
                    logger.info(f"Saved {len(final_results)} results to database")
                except Exception as e:
                    logger.error(f"Failed to save to database: {e}")
                    
        except Exception as e:
            self.page.screenshot(path="scrape_error.png")
            logger.error(f"Failed to scrape search results: {str(e)}")
            raise

    def scrape_comments_from_page(self, max_comments=MAX_COMMENTS_PER_VIDEO):
        """Scrape comments from the currently open video post page."""
        logger.info(f"Attempting to scrape up to {max_comments} comments...")
        comments = []
        try:
            # Wait for comments section with more specific selectors
            comment_container_selectors = [
                'div[data-e2e="comment-list"]',
                'div.css-7whb78-DivCommentListContainer',
                'div[class*="DivCommentListContainer"]',
                '#main-content-video_detail div.css-7whb78-DivCommentListContainer',
                'div.css-x4xlc7-DivCommentContainer div.css-7whb78-DivCommentListContainer'
            ]

            comment_container = None
            for selector in comment_container_selectors:
                try:
                    comment_container = self.page.wait_for_selector(selector, timeout=SEARCH_TIMEOUT)
                    if comment_container:
                        break
                except:
                    continue

            if not comment_container:
                return comments

            # Scroll to load comments
            last_height = self.page.evaluate('document.body.scrollHeight')
            comments_loaded = 0
            scroll_attempts = 0
            max_scroll_attempts = 5
            
            while comments_loaded < max_comments and scroll_attempts < max_scroll_attempts:
                self._random_delay()
                
                self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                self.page.wait_for_timeout(SCROLL_TIMEOUT)
                
                # Updated comment selectors to match the structure
                comment_selectors = [
                    'div[data-e2e="comment-item"]',
                    'div[class*="DivCommentItem"]',
                    'div[class*="DivCommentObjectWrapper"]',
                    'div.css-7whb78-DivCommentListContainer > div',
                    '#main-content-video_detail div.css-7whb78-DivCommentListContainer > div'
                ]

                comment_elements = []
                for selector in comment_selectors:
                    try:
                        elements = self.page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            comment_elements = elements
                            break
                    except Exception as e:
                        continue

                comments_loaded = len(comment_elements)
                
                new_height = self.page.evaluate('document.body.scrollHeight')
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                last_height = new_height
                
                if comments_loaded >= max_comments:
                    break

            # Extract comment data with updated selectors
            for index, comment_elem in enumerate(comment_elements[:max_comments]):
                try:
                    self._random_delay()
                    
                    # Extract username with updated selectors
                    username = ""
                    username_selectors = [
                        'span[data-e2e="comment-username"]',
                        'div[data-e2e="comment-username-1"] p',
                        'span[class*="SpanCommentUsername"]',
                        'a[class*="CommentUsername"]',
                        'span[class*="CommentUsername"]',
                        'div.css-1c7j74y-DivCommentUserInfo a',
                        'div.css-1c7j74y-DivCommentUserInfo span'
                    ]

                    for selector in username_selectors:
                        try:
                            user_elem = comment_elem.query_selector(selector)
                            if user_elem:
                                username = user_elem.inner_text().strip()
                                if username:
                                    break
                        except Exception:
                            continue

                    # Extract comment text with updated selectors
                    comment_text = ""
                    text_selectors = [
                        'p[data-e2e="comment-text"]',
                        'span[data-e2e="comment-level-1"] p',
                        'p[class*="CommentText"]',
                        'span[class*="CommentText"]',
                        'div[class*="CommentText"]',
                        'div.css-1c7j74y-DivCommentUserInfo + div p',
                        'div.css-1c7j74y-DivCommentUserInfo + div span'
                    ]

                    for selector in text_selectors:
                        try:
                            text_elem = comment_elem.query_selector(selector)
                            if text_elem:
                                comment_text = text_elem.inner_text().strip()
                                if comment_text:
                                    break
                        except Exception:
                            continue

                    # Extract date with updated selectors
                    date = ""
                    date_selectors = [
                        # Exact selectors from TikTok
                        'div.css-1lglotn-DivCommentSubContentWrapper span.TUXText',
                        'div.css-1lglotn-DivCommentSubContentWrapper span[class*="TUXText"]',
                        'div.css-1lglotn-DivCommentSubContentWrapper span[style*="color: var(--ui-text-3)"]',
                        'div.css-1ivw6bb-DivCommentSubContentSplitWrapper div.css-1lglotn-DivCommentSubContentWrapper span',
                        'div.css-1k8xzzl-DivCommentContentWrapper div.css-1lglotn-DivCommentSubContentWrapper span',
                        'div.css-1gstnae-DivCommentItemWrapper div.css-1lglotn-DivCommentSubContentWrapper span',
                        # Full path selectors
                        'div.css-7whb78-DivCommentListContainer div.css-1lglotn-DivCommentSubContentWrapper span',
                        'div.css-x4xlc7-DivCommentContainer div.css-1lglotn-DivCommentSubContentWrapper span',
                        'div.css-1senhbu-DivLeftContainer div.css-1lglotn-DivCommentSubContentWrapper span',
                        'div.css-12kupwv-DivContentContainer div.css-1lglotn-DivCommentSubContentWrapper span',
                        '#main-content-video_detail div.css-1lglotn-DivCommentSubContentWrapper span',
                        # Style-based selectors
                        'span.TUXText.TUXText--tiktok-sans.TUXText--weight-normal[style*="color: var(--ui-text-3)"]',
                        'span[class*="TUXText"][style*="color: var(--ui-text-3)"]',
                        'span[class*="TUXText"][style*="font-size: 14px"]',
                        'span[style*="color: var(--ui-text-3)"][style*="font-size: 14px"]',
                        'span[style*="text-wrap: nowrap"]',
                        # Previous selectors as fallback
                        'span[data-e2e="comment-time"]',
                        'span[class*="CommentTime"]',
                        'div[class*="DivCommentTime"]'
                    ]

                    for selector in date_selectors:
                        try:
                            date_elem = comment_elem.query_selector(selector)
                            if date_elem:
                                date_text = date_elem.inner_text().strip()
                                # Check for various date formats
                                if any(pattern in date_text.lower() for pattern in ['d', 'h', 'm', 'w', 'mo', 'y', 'ago', 'min', 'sec', 'hour', 'day', 'week', 'month', 'year']):
                                    date = date_text
                                    logger.debug(f"Found date using selector: {selector}")
                                    break
                        except Exception:
                            continue

                    # Extract likes with updated selectors
                    likes = ""
                    likes_selectors = [
                        # Exact selectors from TikTok
                        'div.css-1nd5cw-DivLikeContainer span.TUXText',
                        'div.css-1nd5cw-DivLikeContainer span[class*="TUXText"]',
                        'div.css-1nd5cw-DivLikeContainer span[style*="color: var(--ui-text-3)"]',
                        'div.css-1ivw6bb-DivCommentSubContentSplitWrapper div.css-1nd5cw-DivLikeContainer span',
                        'div.css-1k8xzzl-DivCommentContentWrapper div.css-1nd5cw-DivLikeContainer span',
                        'div.css-1gstnae-DivCommentItemWrapper div.css-1nd5cw-DivLikeContainer span',
                        # Full path selectors
                        'div.css-7whb78-DivCommentListContainer div.css-1nd5cw-DivLikeContainer span',
                        'div.css-x4xlc7-DivCommentContainer div.css-1nd5cw-DivLikeContainer span',
                        'div.css-1senhbu-DivLeftContainer div.css-1nd5cw-DivLikeContainer span',
                        'div.css-12kupwv-DivContentContainer div.css-1nd5cw-DivLikeContainer span',
                        '#main-content-video_detail div.css-1nd5cw-DivLikeContainer span',
                        # Style-based selectors
                        'span.TUXText.TUXText--tiktok-sans.TUXText--weight-normal[style*="color: var(--ui-text-3)"]',
                        'span[class*="TUXText"][style*="color: var(--ui-text-3)"]',
                        'span[class*="TUXText"][style*="font-size: 14px"]',
                        'span[style*="color: var(--ui-text-3)"][style*="font-size: 14px"]',
                        'span[style*="text-wrap: nowrap"]',
                        # Previous selectors as fallback
                        'span[data-e2e="comment-like-count"]',
                        'span[class*="CommentLikeCount"]',
                        'button[data-e2e="comment-like-button"] strong',
                        'div[data-e2e="comment-action-bar"] strong',
                        'div[class*="DivCommentAction"] strong'
                    ]

                    for selector in likes_selectors:
                        try:
                            likes_elem = comment_elem.query_selector(selector)
                            if likes_elem:
                                likes_text = likes_elem.inner_text().strip()
                                # Check for various number formats
                                if likes_text.isdigit() or \
                                   ('K' in likes_text and len(likes_text) > 1) or \
                                   ('M' in likes_text and len(likes_text) > 1) or \
                                   ('B' in likes_text and len(likes_text) > 1) or \
                                   ('.' in likes_text and any(c.isdigit() for c in likes_text)):
                                    likes = likes_text
                                    logger.debug(f"Found likes using selector: {selector}")
                                    break
                        except Exception:
                            continue

                    # Debug print for each selector attempt
                    logger.debug(f"Comment {index + 1} - Date selectors tried: {len(date_selectors)}")
                    logger.debug(f"Comment {index + 1} - Likes selectors tried: {len(likes_selectors)}")
                    logger.debug(f"Comment {index + 1} - Final date: {date}")
                    logger.debug(f"Comment {index + 1} - Final likes: {likes}")

                    # Print the HTML structure for debugging
                    try:
                        comment_html = comment_elem.inner_html()
                        logger.debug(f"Comment {index + 1} HTML structure:\n{comment_html}")
                    except Exception as e:
                        logger.error(f"Failed to get HTML structure: {e}")

                    comment_data = {
                        "username": username,
                        "text": comment_text,
                        "date": date,
                        "likes": likes
                    }
                    
                    # Print debug info for each comment
                    self._print_debug_info(f"Comment {index + 1}", comment_data)
                    
                    comments.append(comment_data)
                    
                except Exception as e:
                    logger.error(f"Failed to process comment {index}: {e}")
                    continue
            
            return comments
            
        except Exception as e:
            logger.error(f"Error during comment scraping: {e}")
            self.page.screenshot(path="comment_scraping_error.png")
            return comments

    def close(self):
        """Close the browser and context."""
        logger.info("Closing Playwright browser and context...")
        
        if self.page:
            try:
                self.page.close()
            except Exception as e:
                logger.warning(f"Failed to close page: {e}")
                
        if self.context:
            try:
                self.context.close()
            except Exception as e:
                logger.warning(f"Failed to close context: {e}")

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                logger.warning(f"Failed to stop Playwright: {e}")
