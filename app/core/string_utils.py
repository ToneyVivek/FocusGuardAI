def normalize_email(email: str) -> str:
    """
    Normalize email address by trimming whitespace and converting to lowercase.
    Email addresses are case-insensitive per RFC 5321.
    
    Args:
        email: Raw email string
        
    Returns:
        Normalized email string (lowercase, trimmed)
        
    Raises:
        ValueError: If email is empty or only whitespace
    """
    if not email:
        raise ValueError("Email cannot be empty")
    
    normalized = email.strip().lower()
    
    if not normalized:
        raise ValueError("Email cannot be only whitespace")
    
    return normalized
