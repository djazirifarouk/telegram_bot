import re
from config.settings import NESTED_FIELD_STRUCTURES


def validate_date_format(date_str: str) -> tuple[bool, str]:
    """
    Validate date format YYYY-MM.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str or date_str.lower() in ['skip', 'empty']:
        return True, ""
    
    if not re.match(r'^\d{4}-\d{2}$', date_str):
        return False, "Invalid format. Please use YYYY-MM (e.g., 2024-01)"
    
    try:
        year, month = date_str.split('-')
        year = int(year)
        month = int(month)
        
        if year < 1950 or year > 2050:
            return False, f"Year must be between 1950 and 2050. You entered: {year}"
        
        if month < 1 or month > 12:
            return False, f"Month must be between 01 and 12. You entered: {month:02d}"
        
        return True, ""
    except Exception as e:
        return False, f"Error parsing date: {str(e)}"


def validate_subscription_date(date_str: str) -> tuple[bool, str]:
    """
    Validate subscription date format YYYY-MM-DD.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    from datetime import datetime
    
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False, "Invalid format. Please use YYYY-MM-DD (e.g., 2024-12-31)"
    
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True, ""
    except ValueError:
        return False, f"Invalid date: {date_str}"


def is_field_optional(field_type: str, field_name: str) -> bool:
    """
    Check if a field is optional.
    
    Args:
        field_type: Type of nested field (roles, education, etc.)
        field_name: Name of the field
        
    Returns:
        True if field is optional
    """
    structure = NESTED_FIELD_STRUCTURES.get(field_type, {})
    optional_fields = structure.get("optional", [])
    return field_name in optional_fields


def get_field_prompt(
    field_type: str,
    field_name: str,
    labels: dict,
    is_editing: bool = False,
    current_value: str = ""
) -> str:
    """
    Generate appropriate prompt text for a field.
    
    Args:
        field_type: Type of nested field
        field_name: Name of the field
        labels: Dictionary of field labels
        is_editing: Whether this is an edit operation
        current_value: Current value if editing
        
    Returns:
        Formatted prompt string
    """
    label = labels.get(field_name, field_name.title())
    optional = is_field_optional(field_type, field_name)
    
    prompt_parts = []
    
    if is_editing and current_value:
        prompt_parts.append(f"Current: *{current_value}*\n")
    
    prompt_parts.append(f"📝 Enter *{label}*:")
    
    # Add format hint for date fields
    structure = NESTED_FIELD_STRUCTURES.get(field_type, {})
    field_types = structure.get("types", {})
    if field_name in field_types and field_types[field_name] == "date":
        prompt_parts.append("\n_Format: YYYY-MM (e.g., 2024-01)_")
    
    if optional:
        prompt_parts.append("\n\n💡 _Send 'skip' or 'empty' to leave blank_")
    
    return "".join(prompt_parts)
