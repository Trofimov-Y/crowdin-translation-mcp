"""String classification module."""

from typing import List, Literal
from enum import Enum


class StringType(str, Enum):
    """Types of strings for translation."""
    REGULAR = "regular"
    LANGUAGE_NAME = "language"
    PROPER_NAME = "name"
    BRAND = "brand"
    TECHNICAL = "technical"


class StringClassifier:
    """Classifies strings for appropriate translation strategy."""
    
    # Common language names (keep as-is)
    LANGUAGE_NAMES = {
        "english", "spanish", "français", "french", "deutsch", "german",
        "italiano", "italian", "português", "portuguese", "中文", "chinese",
        "русский", "russian", "日本語", "japanese", "한국어", "korean",
        "العربية", "arabic", "עברית", "hebrew", "हिन्दी", "hindi"
    }
    
    def __init__(self, names: List[str] = None, brands: List[str] = None):
        """Initialize classifier with custom lists."""
        self.known_names = set(names or [])
        self.known_brands = set(brands or [])
    
    def classify(self, text: str, key: str = "") -> StringType:
        """
        Classify a string to determine translation strategy.
        
        Args:
            text: The string to classify
            key: Optional translation key for context
            
        Returns:
            StringType indicating the classification
        """
        text_lower = text.lower().strip()
        
        # Check for language names
        if text_lower in self.LANGUAGE_NAMES:
            return StringType.LANGUAGE_NAME
        
        # Check for known proper names
        if text in self.known_names:
            return StringType.PROPER_NAME
        
        # Check for known brands
        if text in self.known_brands:
            return StringType.BRAND
        
        # Check if looks like a proper name (capitalized words)
        words = text.split()
        if len(words) <= 3 and all(w[0].isupper() for w in words if w):
            # Likely a proper name (e.g., "John Smith")
            return StringType.PROPER_NAME
        
        # Check for technical patterns in key
        if key and any(pattern in key.lower() for pattern in ["api", "url", "key", "id", "uuid"]):
            return StringType.TECHNICAL
        
        # Default to regular text
        return StringType.REGULAR
    
    def should_translate(self, string_type: StringType) -> bool:
        """Determine if a string type should be translated."""
        return string_type == StringType.REGULAR
    
    def needs_confirmation(self, string_type: StringType) -> bool:
        """Determine if a string type needs user confirmation."""
        return string_type == StringType.LANGUAGE_NAME
