"""
Test script for the ProxyScraper module.
Demonstrates fetching URLs with retry logic and error handling.
"""

import json
import logging
from scrapers import ProxyScraper, fetch_url, fetch_urls

# Set logging to see detailed output
logging.basicConfig(level=logging.DEBUG)

def test_single_url():
    """Test fetching a single URL."""
    print("\n" + "="*60)
    print("TEST 1: Single URL Fetch")
    print("="*60)
    
    scraper = ProxyScraper()
    
    # Test with a real website
    test_url = "https://www.oatly.com"
    print(f"\nFetching: {test_url}")
    
    result = scraper.fetch(test_url)
    
    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Status Code: {result['status_code']}")
    print(f"  Retries Used: {result['retries_used']}")
    print(f"  Content Length: {len(result['content']) if result['content'] else 0} bytes")
    
    if result['error']:
        print(f"  Error: {result['error']}")
    
    if result['content']:
        print(f"  Content Preview: {result['content'][:200]}...")
    
    return result


def test_multiple_urls():
    """Test fetching multiple URLs."""
    print("\n" + "="*60)
    print("TEST 2: Multiple URLs Fetch (Batch)")
    print("="*60)
    
    scraper = ProxyScraper()
    
    test_urls = [
        "https://www.oatly.com",
        "https://www.alpro.com",
        "https://www.ripplefoods.com",
    ]
    
    print(f"\nFetching {len(test_urls)} URLs...")
    results = scraper.fetch_batch(test_urls)
    
    print(f"\nResults Summary:")
    for i, result in enumerate(results, 1):
        status = "✓" if result['success'] else "✗"
        print(f"  {status} [{i}] {result['url']}")
        if result['success']:
            print(f"      Status: {result['status_code']}, Size: {len(result['content'])} bytes")
        else:
            print(f"      Error: {result['error']}")
    
    # Show error log
    if scraper.get_error_log():
        print(f"\nError Log ({len(scraper.get_error_log())} entries):")
        for error in scraper.get_error_log():
            print(f"  - {error['timestamp']}: {error['error']} (retry {error['retry_attempt']})")
    
    # Show stats
    stats = scraper.get_stats()
    print(f"\nStats:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Total Errors: {stats['total_errors']}")
    
    return results


def test_error_handling():
    """Test error handling with invalid URLs."""
    print("\n" + "="*60)
    print("TEST 3: Error Handling (Invalid URLs)")
    print("="*60)
    
    scraper = ProxyScraper()
    
    invalid_urls = [
        "https://this-domain-does-not-exist-12345.com",
        "https://www.example.com/nonexistent-page-xyz",
    ]
    
    print(f"\nTesting error handling with invalid URLs...")
    results = scraper.fetch_batch(invalid_urls)
    
    print(f"\nError Handling Results:")
    for result in results:
        print(f"  URL: {result['url']}")
        print(f"  Success: {result['success']}")
        print(f"  Error: {result['error']}")
        print(f"  Retries Used: {result['retries_used']}")
        print()


def test_convenience_functions():
    """Test convenience wrapper functions."""
    print("\n" + "="*60)
    print("TEST 4: Convenience Functions")
    print("="*60)
    
    print("\nTesting fetch_url() function...")
    result = fetch_url("https://www.oatly.com")
    print(f"  Success: {result['success']}")
    print(f"  Content Length: {len(result['content']) if result['content'] else 0} bytes")
    
    print("\nTesting fetch_urls() function...")
    results = fetch_urls([
        "https://www.oatly.com",
        "https://www.alpro.com",
    ])
    print(f"  Fetched {len(results)} URLs")
    print(f"  Successful: {sum(1 for r in results if r['success'])}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ProxyScraper Module Test Suite")
    print("="*60)
    
    # Run tests
    # Uncomment the tests you want to run
    
    # test_single_url()
    # test_multiple_urls()
    # test_error_handling()
    # test_convenience_functions()
    
    print("\n" + "="*60)
    print("Note: Tests are commented out to avoid unnecessary API calls.")
    print("Uncomment test functions in __main__ to run them.")
    print("="*60)
