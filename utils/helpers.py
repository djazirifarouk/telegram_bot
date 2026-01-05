def resolve_lookup(value: str) -> tuple[str, str]:
    """
    Determine if value is email or phone number.
    
    Args:
        value: Input string (email or phone)
        
    Returns:
        Tuple of (field_name, cleaned_value)
    """
    value = value.strip()
    if "@" in value:
        return "alias_email", value.lower()
    digits = "".join(c for c in value if c.isdigit())
    return "whatsapp", digits


def chunk_text(text: str, chunk_size: int = 4000) -> list[str]:
    """
    Split text into Telegram-safe chunks.
    
    Args:
        text: Text to split
        chunk_size: Maximum size per chunk
        
    Returns:
        List of text chunks
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
