"""
Domain normalization service for analytics consistency.

This service ensures all website domains are stored in a consistent format
for accurate reporting and analytics aggregation.

Normalization Strategy:
1. Convert to lowercase
2. Trim whitespace
3. Remove trailing dots
4. Remove "www." prefix (common but not meaningful for analytics)
5. Preserve meaningful subdomains (mail.google.com, m.facebook.com)
6. Validate domain format

Future Considerations:
- International domain names (IDN) support
- Custom organization-specific normalization rules
- Domain alias mapping (e.g., fb.com -> facebook.com)
"""

import logging
import re

logger = logging.getLogger(__name__)


class DomainNormalizationService:
    """
    Centralized service for normalizing website domains.
    
    All analytics writes must use this service to ensure consistency.
    """
    
    # Common prefixes to remove (non-meaningful for analytics)
    _PREFIXES_TO_REMOVE = ["www."]
    
    # Meaningful subdomains to preserve (service-specific)
    # These subdomains have different categorization/productivity
    _MEANINGFUL_SUBDOMAINS = {
        "mail",  # mail.google.com vs google.com
        "m",     # m.facebook.com vs facebook.com
        "api",   # api.github.com vs github.com
        "blog",  # blog.medium.com vs medium.com
        "docs",  # docs.python.org vs python.org
        "dev",   # dev.to
        "support",  # support.atlassian.com
        "help",  # help.github.com
    }
    
    @classmethod
    def normalize_domain(cls, domain: str) -> str:
        """
        Normalize a website domain for consistent storage and reporting.
        
        Normalization steps:
        1. Trim whitespace
        2. Convert to lowercase
        3. Remove trailing dots
        4. Remove "www." prefix
        5. Validate domain format
        6. Return normalized domain
        
        Args:
            domain: Raw domain string (e.g., "WWW.GITHUB.COM", "www.github.com")
            
        Returns:
            Normalized domain string (e.g., "github.com", "mail.google.com")
            
        Raises:
            ValueError: If domain is invalid after normalization
        """
        if not domain:
            raise ValueError("Domain cannot be empty")
        
        # Step 1: Trim whitespace
        normalized = domain.strip()
        
        # Step 2: Convert to lowercase
        normalized = normalized.lower()
        
        # Step 3: Remove trailing dots
        normalized = normalized.rstrip(".")
        
        # Step 4: Remove "www." prefix (non-meaningful for analytics)
        for prefix in cls._PREFIXES_TO_REMOVE:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                logger.debug(f"Removed prefix '{prefix}' from domain: {domain}")
                break
        
        # Step 5: Validate domain format
        if not cls._is_valid_domain(normalized):
            raise ValueError(f"Invalid domain format: {domain}")
        
        logger.debug(f"Normalized domain: {domain} -> {normalized}")
        return normalized
    
    @classmethod
    def _is_valid_domain(cls, domain: str) -> bool:
        """
        Validate domain format using regex.
        
        Allows:
        - Standard domains: github.com, google.com
        - Subdomains: mail.google.com, api.github.com
        - International domains: café.com
        
        Rejects:
        - IP addresses
        - Invalid characters
        - Malformed structures
        """
        # Basic length check
        if len(domain) < 3 or len(domain) > 255:
            return False
        
        # Regex pattern for domain validation
        # Allows: subdomain.domain.tld, international domains
        # Rejects: IP addresses, invalid characters
        domain_pattern = r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$'
        
        if not re.match(domain_pattern, domain):
            return False
        
        # Reject if starts/ends with hyphen or has consecutive dots
        if domain.startswith('-') or domain.endswith('-'):
            return False
        if '..' in domain:
            return False
        
        return True
    
    @classmethod
    def should_preserve_subdomain(cls, domain: str) -> bool:
        """
        Determine if a subdomain should be preserved for analytics purposes.
        
        Some subdomains have different categorization or productivity:
        - mail.google.com (COMMUNICATION/PRODUCTIVE) vs google.com (SEARCH_ENGINE/NEUTRAL)
        - m.facebook.com (SOCIAL_MEDIA/NON_PRODUCTIVE) vs facebook.com (SOCIAL_MEDIA/NON_PRODUCTIVE)
        
        Args:
            domain: Normalized domain string
            
        Returns:
            True if subdomain should be preserved, False otherwise
        """
        parts = domain.split('.')
        if len(parts) < 2:
            return False
        
        subdomain = parts[0]
        return subdomain in cls._MEANINGFUL_SUBDOMAINS
    
    @classmethod
    def get_base_domain(cls, domain: str) -> str:
        """
        Extract the base domain (second-level domain + TLD).
        
        Useful for grouping analytics by domain regardless of subdomain.
        
        Args:
            domain: Normalized domain string (e.g., "mail.google.com")
            
        Returns:
            Base domain (e.g., "google.com")
        """
        parts = domain.split('.')
        if len(parts) < 2:
            return domain
        
        # For domains like "mail.google.com", return "google.com"
        # For domains like "github.com", return "github.com"
        if len(parts) == 2:
            return domain
        
        # Extract last two parts (domain + TLD)
        return '.'.join(parts[-2:])


# Singleton instance for consistency
domain_normalization_service = DomainNormalizationService()
