# Twitter Web Scraping Project

A professional and scalable Twitter scraping project that collects tweets and stores them in MongoDB Atlas.

## Features

- Automated Twitter login and navigation
- Tweet data extraction (text, metrics, hashtags, etc.)
- MongoDB Atlas integration for data storage
- JSON backup of scraped data
- Comprehensive logging
- Error handling and recovery
- Configurable settings

## Project Structure

```
twitter_scraper/
├── config.py           # Configuration settings
├── database.py         # MongoDB database operations
├── scraper.py          # Twitter scraping functionality
├── main.py            # Main script
├── requirements.txt    # Project dependencies
├── .env               # Environment variables
└── README.md          # Project documentation
```

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- Twitter account credentials
- MongoDB Atlas account

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root directory with your credentials:
```
TWITTER_USERNAME=your_username_or_email
TWITTER_PASSWORD=your_password
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
```

3. Configure settings in `config.py` if needed:
- MAX_POSTS: Number of posts to scrape
- SCROLL_PAUSE_TIME: Time to wait between scrolls
- BROWSER_WAIT_TIME: Maximum time to wait for elements
- VIEW_RESULTS_TIME: Time to keep browser open after scraping

## Usage

Run the main script:
```bash
python main.py
```

The script will:
1. Initialize the database connection
2. Open Chrome browser
3. Log in to Twitter
4. Navigate to your profile
5. Scrape tweets and save them to MongoDB
6. Create a JSON backup
7. Log all operations to twitter_scraper.log

## Data Storage

- Tweets are stored in MongoDB Atlas
- Each tweet includes:
  - Text content
  - Timestamp
  - Username and handle
  - Engagement metrics (replies, retweets, likes, views)
  - Hashtags
  - Scraping metadata

## Logging

- All operations are logged to `twitter_scraper.log`
- Log format: `timestamp - module - level - message`
- Log levels: INFO, ERROR, DEBUG

## Error Handling

- Comprehensive error handling for all operations
- Automatic cleanup of resources
- Detailed error logging
- Graceful failure recovery
