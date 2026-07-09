import logging
from typing import Optional

from app.models.models import ProductivityClassification, WebsiteCategory

logger = logging.getLogger(__name__)


class WebsiteClassificationService:
    """
    Centralized service for classifying websites by category and productivity.
    
    This service moves business logic from the browser extension to the backend,
    ensuring consistent classification and easier rule updates.
    
    Future expansion:
    - Add database-driven rules
    - Add ML-based classification
    - Add custom organization-specific rules
    - Add subdomain-specific rules
    """
    
    # Domain-based classification rules
    # Format: {domain: (category, productivity)}
    _DOMAIN_RULES = {
        # Development
        "github.com": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "gitlab.com": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "bitbucket.org": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "stackoverflow.com": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "dev.to": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "medium.com": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "codepen.io": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "replit.com": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        
        # AI Tools
        "chat.openai.com": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        "openai.com": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        "anthropic.com": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        "huggingface.co": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        "perplexity.ai": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        "claude.ai": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        
        # Communication
        "slack.com": (WebsiteCategory.COMMUNICATION, ProductivityClassification.PRODUCTIVE),
        "microsoft.com": (WebsiteCategory.COMMUNICATION, ProductivityClassification.PRODUCTIVE),
        "teams.microsoft.com": (WebsiteCategory.COMMUNICATION, ProductivityClassification.PRODUCTIVE),
        "zoom.us": (WebsiteCategory.COMMUNICATION, ProductivityClassification.PRODUCTIVE),
        "meet.google.com": (WebsiteCategory.COMMUNICATION, ProductivityClassification.PRODUCTIVE),
        
        # Social Media
        "facebook.com": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        "instagram.com": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        "twitter.com": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        "x.com": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        "linkedin.com": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NEUTRAL),
        "tiktok.com": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        "reddit.com": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        
        # Entertainment
        "youtube.com": (WebsiteCategory.ENTERTAINMENT, ProductivityClassification.NON_PRODUCTIVE),
        "netflix.com": (WebsiteCategory.ENTERTAINMENT, ProductivityClassification.NON_PRODUCTIVE),
        "twitch.tv": (WebsiteCategory.ENTERTAINMENT, ProductivityClassification.NON_PRODUCTIVE),
        "spotify.com": (WebsiteCategory.ENTERTAINMENT, ProductivityClassification.NON_PRODUCTIVE),
        
        # Search Engines
        "google.com": (WebsiteCategory.SEARCH_ENGINE, ProductivityClassification.NEUTRAL),
        "bing.com": (WebsiteCategory.SEARCH_ENGINE, ProductivityClassification.NEUTRAL),
        "duckduckgo.com": (WebsiteCategory.SEARCH_ENGINE, ProductivityClassification.NEUTRAL),
        
        # Shopping
        "amazon.com": (WebsiteCategory.SHOPPING, ProductivityClassification.NON_PRODUCTIVE),
        "ebay.com": (WebsiteCategory.SHOPPING, ProductivityClassification.NON_PRODUCTIVE),
        "etsy.com": (WebsiteCategory.SHOPPING, ProductivityClassification.NON_PRODUCTIVE),
        
        # News
        "cnn.com": (WebsiteCategory.NEWS, ProductivityClassification.NEUTRAL),
        "bbc.com": (WebsiteCategory.NEWS, ProductivityClassification.NEUTRAL),
        "nytimes.com": (WebsiteCategory.NEWS, ProductivityClassification.NEUTRAL),
        "reuters.com": (WebsiteCategory.NEWS, ProductivityClassification.NEUTRAL),
    }
    
    # Keyword-based classification for unknown domains
    _KEYWORD_RULES = {
        # Development keywords
        "github": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "gitlab": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "stack": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "dev": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "code": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        "api": (WebsiteCategory.DEVELOPMENT, ProductivityClassification.PRODUCTIVE),
        
        # AI keywords
        "openai": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        "claude": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        "gpt": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        "llm": (WebsiteCategory.AI_TOOL, ProductivityClassification.PRODUCTIVE),
        
        # Social media keywords
        "facebook": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        "instagram": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        "twitter": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        "social": (WebsiteCategory.SOCIAL_MEDIA, ProductivityClassification.NON_PRODUCTIVE),
        
        # Entertainment keywords
        "youtube": (WebsiteCategory.ENTERTAINMENT, ProductivityClassification.NON_PRODUCTIVE),
        "netflix": (WebsiteCategory.ENTERTAINMENT, ProductivityClassification.NON_PRODUCTIVE),
        "stream": (WebsiteCategory.ENTERTAINMENT, ProductivityClassification.NON_PRODUCTIVE),
        "video": (WebsiteCategory.ENTERTAINMENT, ProductivityClassification.NON_PRODUCTIVE),
        
        # Shopping keywords
        "shop": (WebsiteCategory.SHOPPING, ProductivityClassification.NON_PRODUCTIVE),
        "store": (WebsiteCategory.SHOPPING, ProductivityClassification.NON_PRODUCTIVE),
        "buy": (WebsiteCategory.SHOPPING, ProductivityClassification.NON_PRODUCTIVE),
    }
    
    @classmethod
    def classify_website(cls, domain: str) -> tuple[WebsiteCategory, ProductivityClassification]:
        """
        Classify a website by domain.
        
        Args:
            domain: Website domain (e.g., "github.com")
            
        Returns:
            Tuple of (category, productivity_classification)
        """
        # Normalize domain
        normalized_domain = domain.lower().strip()
        
        # Check exact domain match
        if normalized_domain in cls._DOMAIN_RULES:
            category, productivity = cls._DOMAIN_RULES[normalized_domain]
            logger.debug(f"Domain match: {normalized_domain} -> {category}, {productivity}")
            return category, productivity
        
        # Check keyword match
        for keyword, (category, productivity) in cls._KEYWORD_RULES.items():
            if keyword in normalized_domain:
                logger.debug(f"Keyword match: {normalized_domain} contains '{keyword}' -> {category}, {productivity}")
                return category, productivity
        
        # Default classification
        logger.debug(f"No match for {normalized_domain}, defaulting to OTHER/NEUTRAL")
        return WebsiteCategory.OTHER, ProductivityClassification.NEUTRAL
    
    @classmethod
    def add_domain_rule(cls, domain: str, category: WebsiteCategory, productivity: ProductivityClassification) -> None:
        """
        Add or update a domain classification rule.
        
        This method allows runtime rule updates without code changes.
        Future: Move to database for persistence.
        """
        cls._DOMAIN_RULES[domain.lower()] = (category, productivity)
        logger.info(f"Added domain rule: {domain} -> {category}, {productivity}")
    
    @classmethod
    def add_keyword_rule(cls, keyword: str, category: WebsiteCategory, productivity: ProductivityClassification) -> None:
        """
        Add or update a keyword classification rule.
        
        This method allows runtime rule updates without code changes.
        Future: Move to database for persistence.
        """
        cls._KEYWORD_RULES[keyword.lower()] = (category, productivity)
        logger.info(f"Added keyword rule: {keyword} -> {category}, {productivity}")


# Singleton instance
classification_service = WebsiteClassificationService()
