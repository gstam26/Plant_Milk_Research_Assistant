"""
Text processing module for cleaning and extracting relevant content from HTML.
Removes boilerplate, scripts, navigation, and limits text to configurable length.
"""

import logging
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from config import MAX_TEXT_LENGTH, LOG_LEVEL, LOG_FILE

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


class TextProcessor:
    """
    Process raw HTML to extract clean, relevant text content.
    Removes boilerplate, scripts, navigation, and enforces length limits.
    """
    
    def __init__(self, max_length: int = MAX_TEXT_LENGTH):
        """
        Initialize the text processor.
        
        Args:
            max_length: Maximum text length in characters (default from config)
        """
        self.max_length = max_length
        self.stats = {
            "processed": 0,
            "total_chars_removed": 0,
            "avg_chars_before": 0,
            "avg_chars_after": 0,
        }
        logger.info(f"TextProcessor initialized with max_length={max_length}")
    
    def _remove_unwanted_tags(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Remove unwanted tags (script, style, nav, footer, etc.).
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Cleaned BeautifulSoup object
        """
        # Tags to remove completely
        unwanted_tags = [
            'script', 'style', 'meta', 'link', 'noscript',
            'nav', 'footer', 'header', '.navigation', '.sidebar',
            'iframe', 'object', 'embed',
        ]
        
        for tag in unwanted_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove elements with common boilerplate classes/ids
        boilerplate_patterns = [
            r'nav', r'menu', r'sidebar', r'footer', r'header',
            r'cookie', r'advertisement', r'ad', r'banner',
            r'popup', r'modal', r'newsletter',
        ]
        
        for pattern in boilerplate_patterns:
            # Remove by class
            for element in soup.find_all(class_=re.compile(pattern, re.I)):
                element.decompose()
            
            # Remove by id
            for element in soup.find_all(id=re.compile(pattern, re.I)):
                element.decompose()
        
        return soup
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from HTML.
        Prioritizes: article, main, content divs, then body.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted text content
        """
        # Priority order for content containers
        content_selectors = [
            soup.find('article'),
            soup.find('main'),
            soup.find(class_=re.compile(r'main|content|body-content|article', re.I)),
            soup.find(id=re.compile(r'main|content|body-content|article', re.I)),
            soup.find('body'),
        ]
        
        for selector in content_selectors:
            if selector:
                return selector.get_text(separator='\n', strip=True)
        
        # Fallback to entire document
        return soup.get_text(separator='\n', strip=True)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text (normalize whitespace, remove extra newlines).
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\n\s*\n', '\n', text)  # Remove multiple newlines
        text = re.sub(r' +', ' ', text)  # Remove multiple spaces
        
        # Remove common boilerplate phrases
        boilerplate_phrases = [
            r'skip to (main )?content',
            r'cookie (policy|consent|notice)',
            r'subscribe to our (newsletter|email)',
            r'follow us on',
            r'copyright.*\d{4}',
            r'all rights reserved',
        ]
        
        for phrase in boilerplate_phrases:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)
        
        # Clean up resulting whitespace from removals
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r' +', ' ', text)
        text = text.strip()
        
        return text
    
    def _truncate_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length (default: self.max_length)
            
        Returns:
            Truncated text
        """
        max_len = max_length or self.max_length
        
        if len(text) <= max_len:
            return text
        
        # Truncate at word boundary
        truncated = text[:max_len]
        last_space = truncated.rfind(' ')
        
        if last_space > max_len * 0.8:  # If last space is within 80% of max
            truncated = truncated[:last_space]
        
        return truncated.rstrip() + '...'
    
    def process(self, html: str, max_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Process raw HTML to extract clean text content.
        
        Args:
            html: Raw HTML content
            max_length: Optional max length override
            
        Returns:
            Dictionary with:
                - success: bool
                - text: str (cleaned text)
                - original_length: int
                - final_length: int
                - chars_removed: int
                - error: str (if failed)
        """
        try:
            original_length = len(html)
            logger.debug(f"Processing HTML: {original_length} bytes")
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted tags
            soup = self._remove_unwanted_tags(soup)
            
            # Extract main content
            text = self._extract_main_content(soup)
            
            # Clean text
            text = self._clean_text(text)
            
            # Truncate to max length
            text = self._truncate_text(text, max_length)
            
            final_length = len(text)
            chars_removed = original_length - final_length
            
            # Update stats
            self.stats["processed"] += 1
            self.stats["total_chars_removed"] += chars_removed
            
            logger.info(
                f"✓ HTML processed: {original_length} → {final_length} bytes "
                f"({chars_removed} removed, {(chars_removed/original_length)*100:.1f}%)"
            )
            
            return {
                "success": True,
                "text": text,
                "original_length": original_length,
                "final_length": final_length,
                "chars_removed": chars_removed,
                "error": None,
            }
        
        except Exception as e:
            error_msg = f"Failed to process HTML: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "text": None,
                "original_length": len(html),
                "final_length": 0,
                "chars_removed": 0,
                "error": error_msg,
            }
    
    def process_batch(self, html_list: list, max_length: Optional[int] = None) -> list:
        """
        Process multiple HTML documents.
        
        Args:
            html_list: List of HTML strings
            max_length: Optional max length override
            
        Returns:
            List of processing results
        """
        logger.info(f"Processing batch of {len(html_list)} HTML documents")
        results = []
        
        for i, html in enumerate(html_list, 1):
            logger.debug(f"Batch progress: {i}/{len(html_list)}")
            result = self.process(html, max_length)
            results.append(result)
        
        successful = sum(1 for r in results if r['success'])
        logger.info(
            f"Batch complete: {successful}/{len(html_list)} successful"
        )
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with stats
        """
        if self.stats["processed"] > 0:
            self.stats["avg_chars_before"] = (
                self.stats["total_chars_removed"] / self.stats["processed"]
            )
        
        return self.stats
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = {
            "processed": 0,
            "total_chars_removed": 0,
            "avg_chars_before": 0,
            "avg_chars_after": 0,
        }
        logger.debug("Statistics reset")


# Convenience functions
def process_html(html: str, max_length: Optional[int] = None) -> Dict[str, Any]:
    """
    Process a single HTML document using default processor.
    
    Args:
        html: Raw HTML content
        max_length: Optional max length override
        
    Returns:
        Processing result dictionary
    """
    processor = TextProcessor(max_length or MAX_TEXT_LENGTH)
    return processor.process(html, max_length)


def process_html_batch(html_list: list, max_length: Optional[int] = None) -> list:
    """
    Process multiple HTML documents using default processor.
    
    Args:
        html_list: List of HTML strings
        max_length: Optional max length override
        
    Returns:
        List of processing results
    """
    processor = TextProcessor(max_length or MAX_TEXT_LENGTH)
    return processor.process_batch(html_list, max_length)
