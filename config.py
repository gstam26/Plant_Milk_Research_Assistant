"""
Configuration module for the scraper service.
Manages proxy API settings, timeouts, and retry logic.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Proxy/ScraperAPI Settings
PROXY_API_BASE_URL = os.getenv("PROXY_API_BASE_URL", "http://api.scraperapi.com")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "true").lower() == "true"

# Timeout Settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds

# Retry Settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
INITIAL_RETRY_DELAY = float(os.getenv("INITIAL_RETRY_DELAY", "1"))  # seconds
BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR", "2"))  # exponential backoff multiplier

# Logging Settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "scraper.log")

# Text Processing Settings
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "20000"))  # characters
EXTRACT_MAIN_CONTENT = os.getenv("EXTRACT_MAIN_CONTENT", "true").lower() == "true"

# Proxy-specific settings
PROXY_PARAMS = {
    "api_key": PROXY_API_KEY,
    "render": "false",  # Set to "true" for JavaScript rendering
}

def get_proxy_url(target_url: str) -> str:
    """
    Construct the proxy API URL for a target URL.
    
    Args:
        target_url: The actual URL to scrape
        
    Returns:
        Full proxy API URL with parameters
    """
    if not PROXY_ENABLED:
        return target_url
    
    params = "&".join([f"{k}={v}" for k, v in PROXY_PARAMS.items()])
    return f"{PROXY_API_BASE_URL}?url={target_url}&{params}"
