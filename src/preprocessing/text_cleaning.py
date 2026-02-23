import re
from typing import Optional

class TextCleaner:
    """
    Preprocesses CV and job description texts for fair comparison.
    Designed for junior/entry-level job matching.
    """
    
    def __init__(
        self,
        remove_emails: bool = True,
        remove_phone: bool = True,
        remove_urls: bool = True,
        min_length: int = 50
    ):
        self.remove_emails = remove_emails
        self.remove_phone = remove_phone
        self.remove_urls = remove_urls
        self.min_length = min_length
        
    def clean(self, text: str) -> Optional[str]:
        """
        Clean a single text document.
        
        Args:
            text: Raw text from CV or job description
            
        Returns:
            Cleaned text or None if text is too short/empty
        """
        if not text or not isinstance(text, str):
            return None
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove emails
        if self.remove_emails:
            text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers (various formats)
        if self.remove_phone:
            text = re.sub(r'\+?\d[\d\s\-\(\)]{7,}\d', '', text)
        
        # Remove URLs
        if self.remove_urls:
            text = re.sub(r'http\S+|www\.\S+', '', text)
        
        # Remove special characters but keep spaces and basic punctuation
        text = re.sub(r'[^a-z0-9\s\.\,\-]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Check minimum length
        if len(text) < self.min_length:
            return None
            
        return text
    
    def clean_batch(self, texts: list[str]) -> list[dict]:
        """
        Clean multiple texts and return with metadata.
        
        Args:
            texts: List of raw texts
            
        Returns:
            List of dicts with 'original_index', 'cleaned_text'
        """
        results = []
        for idx, text in enumerate(texts):
            cleaned = self.clean(text)
            if cleaned:
                results.append({
                    'original_index': idx,
                    'cleaned_text': cleaned
                })
        return results


def load_text_file(filepath: str) -> str:
    """Load text from a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def save_cleaned_text(text: str, filepath: str):
    """Save cleaned text to a file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)