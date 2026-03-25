"""Prompt sanitizer for preventing injection attacks in Claude API calls.

All untrusted content (news articles, user questions) MUST be sanitized
before being included in any Claude prompt.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Patterns that could indicate injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"you\s+are\s+now\s+(an?\s+)?unrestricted",
    r"\[system\s*:",
    r"<system>",
    r"print\s+(the\s+)?system\s+prompt",
    r"reveal\s+(your\s+)?instructions",
    r"disable\s+safety",
    r"debug\s+mode",
    r"jailbreak",
    r"DAN\s+mode",
    r"developer\s+mode",
    r"override\s+previous",
    r"disregard\s+(all\s+)?previous",
    r"new\s+instructions?\s*:",
    r"forget\s+(all\s+)?previous",
]

# Maximum lengths
MAX_ARTICLE_LENGTH = 2000
MAX_QUESTION_LENGTH = 500
MAX_ARTICLES_PER_PROMPT = 10


def sanitize_text(text: str, max_length: int = MAX_ARTICLE_LENGTH) -> str:
    """Sanitize untrusted text for safe inclusion in Claude prompts.

    - Strips control characters
    - Truncates to max length
    - Escapes XML-like tags that could confuse prompt boundaries

    Args:
        text: Untrusted input text.
        max_length: Maximum allowed length.

    Returns:
        Sanitized text safe for prompt inclusion.
    """
    if not isinstance(text, str):
        return ""

    # Remove control characters (except newlines and tabs)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Escape XML-like tags that could break prompt boundaries
    cleaned = cleaned.replace('<', '&lt;').replace('>', '&gt;')

    # Truncate
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "... [truncated]"

    return cleaned


def sanitize_question(question: str) -> str:
    """Sanitize a user question for AI Q&A.

    Args:
        question: User-provided question text.

    Returns:
        Sanitized question.
    """
    return sanitize_text(question, max_length=MAX_QUESTION_LENGTH)


def sanitize_articles(articles: list[str]) -> list[str]:
    """Sanitize a list of news articles for prompt injection safety.

    Args:
        articles: List of article text strings.

    Returns:
        Sanitized list (truncated to MAX_ARTICLES_PER_PROMPT).
    """
    sanitized = []
    for article in articles[:MAX_ARTICLES_PER_PROMPT]:
        sanitized.append(sanitize_text(article))
    return sanitized


def detect_injection(text: str) -> bool:
    """Check if text contains potential prompt injection attempts.

    Args:
        text: Text to check.

    Returns:
        True if injection patterns detected.
    """
    lower_text = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower_text, re.IGNORECASE):
            logger.warning("Potential prompt injection detected: %s", pattern)
            return True
    return False


def wrap_in_xml_tags(content: str, tag: str) -> str:
    """Wrap content in XML tags for clear prompt boundaries.

    Args:
        content: The content to wrap.
        tag: The XML tag name (e.g., 'articles', 'question').

    Returns:
        Content wrapped in XML tags.
    """
    return f"<{tag}>\n{content}\n</{tag}>"
