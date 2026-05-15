"""
Web scraper module using proxy API (ScraperAPI or similar).
Implements retry logic, timeout handling, and error logging.
"""

import logging
import time
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from config import (
    PROXY_API_BASE_URL,
    PROXY_API_KEY,
    PROXY_ENABLED,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    INITIAL_RETRY_DELAY,
    BACKOFF_FACTOR,
    LOG_LEVEL,
    LOG_FILE,
    get_proxy_url,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class ScraperTimeoutError(ScraperError):
    """Raised when a request times out."""
    pass


class ScraperRetryableError(ScraperError):
    """Raised when a request fails but might succeed on retry."""
    pass


class ScraperFatalError(ScraperError):
    """Raised when a request fails fatally (do not retry)."""
    pass


class ProxyScraper:
    """
    Web scraper that routes requests through a proxy API.
    Implements retry logic with exponential backoff and timeout handling.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the scraper.
        
        Args:
            api_key: Optional override for proxy API key
            base_url: Optional override for proxy API base URL
        """
        self.api_key = api_key or PROXY_API_KEY
        self.base_url = base_url or PROXY_API_BASE_URL
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        self.initial_delay = INITIAL_RETRY_DELAY
        self.backoff_factor = BACKOFF_FACTOR
        self.request_count = 0
        self.error_log = []
        
        logger.info(
            f"ProxyScraper initialized: base_url={self.base_url}, "
            f"timeout={self.timeout}s, max_retries={self.max_retries}"
        )
    
    def _construct_proxy_url(self, target_url: str) -> str:
        """
        Construct the full proxy API URL.
        
        Args:
            target_url: The URL to scrape
            
        Returns:
            Full proxy API URL with parameters
        """
        if not PROXY_ENABLED:
            return target_url
        
        # URL encode the target URL for the proxy API
        try:
            from urllib.parse import quote
            encoded_url = quote(target_url, safe=':/?#[]@!$&\'()*+,;=')
            params = f"api_key={self.api_key}&render=false"
            return f"{self.base_url}?url={encoded_url}&{params}"
        except Exception as e:
            logger.error(f"Error constructing proxy URL for {target_url}: {e}")
            raise ScraperFatalError(f"Failed to construct proxy URL: {e}")
    
    def _calculate_backoff_delay(self, retry_count: int) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            retry_count: Current retry attempt (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.backoff_factor ** retry_count)
        logger.debug(f"Backoff delay for retry {retry_count + 1}: {delay}s")
        return delay
    
    def _log_error(self, url: str, error: str, retry_count: int):
        """
        Log an error for a URL.
        
        Args:
            url: The target URL
            error: Error description
            retry_count: Current retry attempt
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "error": error,
            "retry_attempt": retry_count + 1,
        }
        self.error_log.append(error_entry)
        logger.warning(f"[Retry {retry_count + 1}] Error for {url}: {error}")
    
    def fetch(self, url: str) -> Dict[str, Any]:
        """
        Fetch webpage content through proxy API with retry logic.
        
        Args:
            url: The target URL to scrape
            
        Returns:
            Dictionary with keys:
                - success: bool
                - content: str (raw HTML) if successful
                - status_code: int (HTTP status)
                - error: str (if failed)
                - retries_used: int
                - url: str (original target URL)
        """
        self.request_count += 1
        proxy_url = self._construct_proxy_url(url)
        
        logger.info(f"[Request {self.request_count}] Fetching: {url}")
        
        for retry_count in range(self.max_retries):
            try:
                start_time = time.time()
                
                # Make request through proxy API
                async def _async_fetch():
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.get(proxy_url, follow_redirects=True)
                        return response
                
                # Use synchronous wrapper for async call
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                response = loop.run_until_complete(_async_fetch())
                elapsed_time = time.time() - start_time
                
                # Check for successful response
                if response.status_code == 200:
                    content = response.text
                    logger.info(
                        f"✓ Successfully fetched {url} "
                        f"({len(content)} bytes, {elapsed_time:.2f}s, "
                        f"retries: {retry_count})"
                    )
                    return {
                        "success": True,
                        "content": content,
                        "status_code": response.status_code,
                        "error": None,
                        "retries_used": retry_count,
                        "url": url,
                        "elapsed_time": elapsed_time,
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.reason_phrase}"
                    self._log_error(url, error_msg, retry_count)
                    
                    # Fatal errors (404, 403, etc.) - don't retry
                    if response.status_code in [403, 404, 401, 410]:
                        raise ScraperFatalError(error_msg)
                    
                    # Retry on server errors
                    raise ScraperRetryableError(error_msg)
            
            except ScraperFatalError as e:
                logger.error(f"✗ Fatal error for {url}: {e}")
                return {
                    "success": False,
                    "content": None,
                    "status_code": None,
                    "error": str(e),
                    "retries_used": retry_count,
                    "url": url,
                }
            
            except httpx.TimeoutException as e:
                self._log_error(url, f"Timeout ({self.timeout}s)", retry_count)
                if retry_count < self.max_retries - 1:
                    delay = self._calculate_backoff_delay(retry_count)
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"✗ Timeout for {url} after {self.max_retries} retries")
                    return {
                        "success": False,
                        "content": None,
                        "status_code": None,
                        "error": f"Timeout after {self.max_retries} retries",
                        "retries_used": retry_count,
                        "url": url,
                    }
            
            except ScraperRetryableError as e:
                if retry_count < self.max_retries - 1:
                    delay = self._calculate_backoff_delay(retry_count)
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"✗ Failed for {url} after {self.max_retries} retries: {e}")
                    return {
                        "success": False,
                        "content": None,
                        "status_code": None,
                        "error": f"Failed after {self.max_retries} retries: {str(e)}",
                        "retries_used": retry_count,
                        "url": url,
                    }
            
            except Exception as e:
                error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
                self._log_error(url, error_msg, retry_count)
                
                if retry_count < self.max_retries - 1:
                    delay = self._calculate_backoff_delay(retry_count)
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"✗ Unexpected error for {url}: {e}")
                    return {
                        "success": False,
                        "content": None,
                        "status_code": None,
                        "error": error_msg,
                        "retries_used": retry_count,
                        "url": url,
                    }
        
        # Should not reach here, but return failed response as fallback
        return {
            "success": False,
            "content": None,
            "status_code": None,
            "error": "Unknown error after all retries",
            "retries_used": self.max_retries,
            "url": url,
        }
    
    def fetch_batch(self, urls: list) -> list:
        """
        Fetch multiple URLs sequentially.
        
        Args:
            urls: List of URLs to fetch
            
        Returns:
            List of fetch results (one per URL)
        """
        logger.info(f"Starting batch fetch of {len(urls)} URLs")
        results = []
        
        for i, url in enumerate(urls, 1):
            logger.debug(f"Batch progress: {i}/{len(urls)}")
            result = self.fetch(url)
            results.append(result)
        
        logger.info(
            f"Batch fetch complete. "
            f"Success: {sum(1 for r in results if r['success'])}/"
            f"{len(results)}"
        )
        return results
    
    def get_error_log(self) -> list:
        """
        Retrieve the error log.
        
        Returns:
            List of error entries
        """
        return self.error_log
    
    def clear_error_log(self):
        """Clear the error log."""
        self.error_log = []
        logger.debug("Error log cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scraper statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            "total_requests": self.request_count,
            "total_errors": len(self.error_log),
            "error_log": self.error_log,
        }


# Convenience functions
def fetch_url(url: str) -> Dict[str, Any]:
    """
    Fetch a single URL using default scraper instance.
    
    Args:
        url: The URL to fetch
        
    Returns:
        Fetch result dictionary
    """
    scraper = ProxyScraper()
    return scraper.fetch(url)


def fetch_urls(urls: list) -> list:
    """
    Fetch multiple URLs using default scraper instance.
    
    Args:
        urls: List of URLs to fetch
        
    Returns:
        List of fetch result dictionaries
    """
    scraper = ProxyScraper()
    return scraper.fetch_batch(urls)
