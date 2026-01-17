"""Utility functions for the Telegram bot."""

import re
from typing import List, Optional


def extract_hashtags(caption: Optional[str]) -> List[str]:
    """
    Extract hashtags from a caption string.
    
    Args:
        caption: The caption text (can be None or empty)
        
    Returns:
        List of hashtags (without the # symbol), lowercase
    """
    if not caption:
        return []
    
    # Find all hashtags using regex
    hashtags = re.findall(r'#(\w+)', caption)
    
    # Return lowercase, unique hashtags
    return list(set(tag.lower() for tag in hashtags))
