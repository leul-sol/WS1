# TikTok Search Scraper

A Python-based scraper for TikTok search results and comments using Playwright with captcha handling.

## Features

- Search TikTok using keywords
- Extract video information (title, URL, likes, etc.)
- Scrape comments from videos
- Handle captchas automatically
- Save results to JSON files
- Detailed logging

## Setup

1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

4. Create a `keywords.txt` file with your search terms (one per line)

5. Replace the SadCaptcha API key in `scraper.py` with your own key:
```python
SADCAPTCHA_API_KEY = "your_api_key_here"
```

## Usage

Run the scraper:
```bash
python main.py
```

The script will:
- Read keywords from `keywords.txt`
- Search TikTok for each keyword
- Scrape video information and comments
- Save results to JSON files (one per keyword)

## Output

Results are saved in JSON files named `tiktok_search_results_{keyword}.json` with the following structure:
```json
[
  {
    "title": "Video title",
    "video_url": "https://tiktok.com/...",
    "like": "1.2K",
    "comment": "123",
    "share": "45",
    "date": "2024-03-21",
    "username": "@username",
    "comments": [
      {
        "username": "@commenter",
        "text": "Comment text",
        "date": "2d",
        "likes": "123"
      }
    ],
    "hashtags": ["#hashtag1", "#hashtag2"]
  }
]
```

## Logging

Logs are saved to `tiktok_scraper.log` and also displayed in the console.

## Error Handling

- The scraper handles network errors, timeouts, and captchas
- Screenshots are saved when errors occur for debugging
- Failed keywords are logged but don't stop the entire process

## Notes

- The scraper uses a persistent browser context to maintain sessions
- Captcha solving is handled automatically using SadCaptcha
- Rate limiting and delays are implemented to avoid blocking 