"""
Test script for TextProcessor module.
Demonstrates HTML cleaning, content extraction, and text truncation.
"""

from text_processor import TextProcessor, process_html, process_html_batch

# Sample HTML documents for testing
SAMPLE_HTML_1 = """
<html>
<head>
    <script>console.log('test');</script>
    <style>body { color: red; }</style>
</head>
<body>
    <nav class="navigation">
        <a href="/">Home</a>
        <a href="/products">Products</a>
    </nav>
    
    <article>
        <h1>Oatly - Plant-Based Milk</h1>
        <p>Oatly is a leading oat milk brand focused on sustainability.</p>
        <p>Our mission is to make it easy for people to choose a more climate positive lifestyle.</p>
        <p>Parent company: Oatly Group AB</p>
        <p>Product types: Oat milk, barista edition, chocolate</p>
    </article>
    
    <footer>
        <p>Copyright 2025 Oatly</p>
        <p>Follow us on social media</p>
    </footer>
    
    <div class="cookie-consent">
        <p>We use cookies. Click to accept.</p>
    </div>
</body>
</html>
"""

SAMPLE_HTML_2 = """
<html>
<body>
    <div class="header">Header Navigation</div>
    <div class="main-content">
        <h1>Alpro - Soy & Plant-Based Milk</h1>
        <p>Alpro specializes in plant-based alternatives to dairy.</p>
        <p>Sustainability claims: Certified B Corp, reducing plastic packaging</p>
        <p>Parent: Danone</p>
    </div>
    <div class="sidebar">Advertisement</div>
    <div class="footer">Copyright notice</div>
</body>
</html>
"""

SAMPLE_HTML_LARGE = """
<html>
<body>
    <article>
        <h1>Long Article</h1>
        <p>""" + " ".join(["Lorem ipsum dolor sit amet, consectetur adipiscing elit."] * 500) + """</p>
    </article>
</body>
</html>
"""


def test_single_html():
    """Test processing a single HTML document."""
    print("\n" + "="*60)
    print("TEST 1: Single HTML Processing")
    print("="*60)
    
    processor = TextProcessor()
    result = processor.process(SAMPLE_HTML_1)
    
    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Original: {result['original_length']} bytes")
    print(f"  Final: {result['final_length']} bytes")
    print(f"  Removed: {result['chars_removed']} ({(result['chars_removed']/result['original_length']*100):.1f}%)")
    
    if result['success']:
        print(f"\nExtracted text:")
        print(f"---")
        print(result['text'][:500])
        print(f"---")


def test_batch_processing():
    """Test processing multiple HTML documents."""
    print("\n" + "="*60)
    print("TEST 2: Batch HTML Processing")
    print("="*60)
    
    processor = TextProcessor()
    html_list = [SAMPLE_HTML_1, SAMPLE_HTML_2]
    results = processor.process_batch(html_list)
    
    print(f"\nProcessed {len(results)} documents:")
    for i, result in enumerate(results, 1):
        status = "✓" if result['success'] else "✗"
        print(f"  {status} [Document {i}]")
        print(f"      Original: {result['original_length']} bytes")
        print(f"      Final: {result['final_length']} bytes")
        if result['error']:
            print(f"      Error: {result['error']}")
    
    # Show stats
    stats = processor.get_stats()
    print(f"\nStatistics:")
    print(f"  Total Processed: {stats['processed']}")
    print(f"  Total Chars Removed: {stats['total_chars_removed']}")


def test_text_truncation():
    """Test text truncation at max length."""
    print("\n" + "="*60)
    print("TEST 3: Text Truncation (Max Length)")
    print("="*60)
    
    processor = TextProcessor(max_length=200)
    result = processor.process(SAMPLE_HTML_LARGE)
    
    print(f"\nWith max_length=200:")
    print(f"  Original: {result['original_length']} bytes")
    print(f"  Final: {result['final_length']} bytes")
    print(f"  Removed: {result['chars_removed']} ({(result['chars_removed']/result['original_length']*100):.1f}%)")
    
    if result['success']:
        print(f"\nTruncated text:")
        print(f"---")
        print(result['text'])
        print(f"---")


def test_boilerplate_removal():
    """Test removal of boilerplate elements."""
    print("\n" + "="*60)
    print("TEST 4: Boilerplate Removal")
    print("="*60)
    
    boilerplate_html = """
    <html>
    <body>
        <nav>Navigation</nav>
        <div class="cookie-banner">Accept cookies</div>
        <article>
            <h1>Brand Name</h1>
            <p>This is the main content we want to extract.</p>
        </article>
        <footer>Copyright 2025</footer>
        <div id="newsletter-signup">Subscribe to our newsletter</div>
    </body>
    </html>
    """
    
    processor = TextProcessor()
    result = processor.process(boilerplate_html)
    
    print(f"\nExtracted text (boilerplate removed):")
    print(f"---")
    print(result['text'])
    print(f"---")
    
    # Check that boilerplate was removed
    text_lower = result['text'].lower()
    assert 'navigation' not in text_lower, "Navigation not removed"
    assert 'cookie' not in text_lower, "Cookie banner not removed"
    assert 'newsletter' not in text_lower, "Newsletter signup not removed"
    assert 'copyright' not in text_lower, "Copyright not removed"
    assert 'brand name' in text_lower, "Main content removed!"
    
    print("✓ Boilerplate successfully removed")


def test_convenience_functions():
    """Test convenience wrapper functions."""
    print("\n" + "="*60)
    print("TEST 5: Convenience Functions")
    print("="*60)
    
    print("\nTesting process_html()...")
    result = process_html(SAMPLE_HTML_1)
    print(f"  Success: {result['success']}")
    print(f"  Text length: {result['final_length']} bytes")
    
    print("\nTesting process_html_batch()...")
    results = process_html_batch([SAMPLE_HTML_1, SAMPLE_HTML_2])
    print(f"  Processed: {len(results)} documents")
    print(f"  Successful: {sum(1 for r in results if r['success'])}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TextProcessor Module Test Suite")
    print("="*60)
    
    test_single_html()
    test_batch_processing()
    test_text_truncation()
    test_boilerplate_removal()
    test_convenience_functions()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
