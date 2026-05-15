# ProxyScraper Module

A robust Python module for fetching webpage content through a proxy API (e.g., ScraperAPI). Includes retry logic with exponential backoff, timeout handling, and comprehensive error logging.

## Features

✅ **Proxy API Integration** - Routes all requests through a configurable proxy endpoint (no direct requests)  
✅ **Retry Logic** - 3 attempts with exponential backoff (1s → 2s → 4s)  
✅ **Timeout Handling** - 30-second timeout per request (configurable)  
✅ **Error Logging** - Comprehensive logging to file and console  
✅ **Batch Processing** - Fetch multiple URLs sequentially  
✅ **Statistics** - Track request counts and errors  
✅ **Async Support** - Uses httpx async client for efficient I/O  

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
# Proxy API Settings
PROXY_API_BASE_URL=https://api.scraperapi.com
PROXY_API_KEY=your_key_here
PROXY_ENABLED=true

# Timeout (seconds)
REQUEST_TIMEOUT=30

# Retry Settings
MAX_RETRIES=3
INITIAL_RETRY_DELAY=1
BACKOFF_FACTOR=2

# Logging
LOG_LEVEL=INFO
LOG_FILE=scraper.log
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `PROXY_API_BASE_URL` | http://api.scraperapi.com | Proxy API endpoint |
| `PROXY_API_KEY` | (empty) | API key for proxy service |
| `PROXY_ENABLED` | true | Enable/disable proxy routing |
| `REQUEST_TIMEOUT` | 30 | Timeout per request (seconds) |
| `MAX_RETRIES` | 3 | Maximum retry attempts |
| `INITIAL_RETRY_DELAY` | 1 | Initial backoff delay (seconds) |
| `BACKOFF_FACTOR` | 2 | Exponential backoff multiplier |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FILE` | scraper.log | Log file path |

## Usage

### Basic Single URL Fetch

```python
from scrapers import ProxyScraper

scraper = ProxyScraper()
result = scraper.fetch("https://example.com")

if result['success']:
    content = result['content']
    print(f"Fetched {len(content)} bytes")
else:
    print(f"Error: {result['error']}")
```

### Batch Fetch Multiple URLs

```python
from scrapers import ProxyScraper

scraper = ProxyScraper()
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
]

results = scraper.fetch_batch(urls)

for result in results:
    print(f"{result['url']}: {'✓' if result['success'] else '✗'}")
```

### Using Convenience Functions

```python
from scrapers import fetch_url, fetch_urls

# Single URL
result = fetch_url("https://example.com")

# Multiple URLs
results = fetch_urls([
    "https://example.com/page1",
    "https://example.com/page2",
])
```

### Error Handling

```python
from scrapers import ProxyScraper

scraper = ProxyScraper()
result = scraper.fetch("https://example.com")

print(f"Success: {result['success']}")
print(f"Status Code: {result['status_code']}")
print(f"Error: {result['error']}")
print(f"Retries Used: {result['retries_used']}")

# Check error log
errors = scraper.get_error_log()
for error in errors:
    print(f"{error['timestamp']}: {error['error']}")
```

## Response Format

The `fetch()` method returns a dictionary with the following structure:

```python
{
    "success": bool,           # Whether the fetch succeeded
    "content": str,            # Raw HTML content (None if failed)
    "status_code": int,        # HTTP status code (None if failed)
    "error": str,              # Error message (None if successful)
    "retries_used": int,       # Number of retries used
    "url": str,                # Original target URL
    "elapsed_time": float,     # Request time in seconds (if successful)
}
```

### Example Response (Success)

```python
{
    "success": True,
    "content": "<html>...</html>",
    "status_code": 200,
    "error": None,
    "retries_used": 0,
    "url": "https://example.com",
    "elapsed_time": 2.34
}
```

### Example Response (Failure)

```python
{
    "success": False,
    "content": None,
    "status_code": None,
    "error": "Failed after 3 retries: HTTP 502: Bad Gateway",
    "retries_used": 3,
    "url": "https://example.com",
}
```

## Retry Logic

The scraper implements intelligent retry logic:

- **Fatal errors** (403, 404, 401, 410) → no retry
- **Server errors** (500, 502, 503) → retry with backoff
- **Timeouts** → retry with backoff
- **Other errors** → retry with backoff

**Backoff calculation**: `delay = initial_delay * (backoff_factor ^ retry_count)`

Example with defaults:
- Retry 1: 1 second
- Retry 2: 2 seconds
- Retry 3: 4 seconds

## Logging

Logs are written to both file and console:

```
2025-05-15 10:30:45 - scrapers - INFO - [Request 1] Fetching: https://example.com
2025-05-15 10:30:47 - scrapers - INFO - ✓ Successfully fetched https://example.com (12345 bytes, 2.34s, retries: 0)
```

## Class API

### ProxyScraper

```python
class ProxyScraper:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None)
    def fetch(self, url: str) -> Dict[str, Any]
    def fetch_batch(self, urls: list) -> list
    def get_error_log(self) -> list
    def clear_error_log()
    def get_stats() -> Dict[str, Any]
```

### Module Functions

```python
fetch_url(url: str) -> Dict[str, Any]
fetch_urls(urls: list) -> list
```

## Error Handling

The module defines custom exceptions:

```python
ScraperError              # Base exception
├── ScraperTimeoutError   # Request timed out
├── ScraperRetryableError # Retryable failure (e.g., 503)
└── ScraperFatalError     # Non-retryable failure (e.g., 404)
```

## Testing

Run the test suite:

```bash
python test_scraper.py
```

Uncomment test functions in `__main__` to run them:
- `test_single_url()` - Fetch a single URL
- `test_multiple_urls()` - Fetch multiple URLs with batch
- `test_error_handling()` - Test error handling
- `test_convenience_functions()` - Test wrapper functions

## Security Notes

🔐 **API Key Security**
- Store `PROXY_API_KEY` in `.env` file
- Never commit `.env` to version control
- Use environment variables in production
- Rotate keys regularly

🔐 **URL Encoding**
- All target URLs are safely URL-encoded
- Proxy API endpoint is always HTTPS
- No credentials are logged

## Performance

- **Async I/O**: Uses httpx async client for non-blocking requests
- **Batch Processing**: Sequential fetching with minimal overhead
- **Resource Efficient**: Reuses connection pooling

## Known Limitations

⚠️ **JavaScript Rendering**: Currently disabled (`render=false`)  
→ To enable, set `render=true` in config

⚠️ **Sequential Batch Processing**: URLs are fetched one at a time  
→ For parallel fetching, use concurrent.futures or asyncio

⚠️ **Rate Limiting**: No built-in rate limiting  
→ Add delays between requests if needed to avoid rate limiting

## Troubleshooting

### API Key Not Working
```
Error: HTTP 401: Unauthorized
```
→ Check `PROXY_API_KEY` in `.env`

### Timeouts
```
Error: Timeout after 3 retries
```
→ Increase `REQUEST_TIMEOUT` in `.env`
→ Check network connectivity

### 403 Forbidden
```
Error: HTTP 403: Forbidden (fatal)
```
→ Website may block scraping
→ Consider enabling JavaScript rendering (`render=true`)

## Future Enhancements

- [ ] Parallel batch fetching (asyncio)
- [ ] Automatic JavaScript rendering detection
- [ ] Response caching
- [ ] Rate limiting
- [ ] Custom headers support
- [ ] Proxy rotation
