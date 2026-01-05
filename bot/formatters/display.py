from config.settings import NESTED_FIELD_STRUCTURES


def format_nested_array(data_list: list, field_type: str) -> str:
    """
    Format nested array data for display.
    
    Args:
        data_list: List of nested data items
        field_type: Type of field (roles, education, etc.)
        
    Returns:
        Formatted string for display
    """
    if not data_list:
        return "None"
    
    structure = NESTED_FIELD_STRUCTURES.get(field_type, {})
    labels = structure.get("labels", {})
    
    result = []
    for idx, item in enumerate(data_list, 1):
        result.append(f"\n*Entry {idx}:*")
        for key, value in item.items():
            label = labels.get(key, key.title())
            result.append(f"  • {label}: {value}")
    
    return "\n".join(result)


def format_applicant_list(users: list, status_emoji: str = "•") -> str:
    """
    Format a list of applicants for display.
    
    Args:
        users: List of user dictionaries
        status_emoji: Emoji to use as bullet point
        
    Returns:
        Formatted string
    """
    if not users:
        return "No applicants found."
    
    return "\n".join([
        f"{status_emoji} {u['first_name']} {u['last_name']}\n"
        f"  📧 `{u['alias_email']}`\n"
        f"  📱 {u.get('whatsapp', 'N/A')}\n"
        for u in users
    ])