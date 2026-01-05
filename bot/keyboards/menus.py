from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.settings import (
    EDITABLE_FIELDS,
    APPLICATION_PLAN_OPTIONS,
    LANGUAGE_PROFICIENCY_OPTIONS
)


def get_main_menu() -> InlineKeyboardMarkup:
    """Get the main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("📋 View Applicants", callback_data="view")],
        [InlineKeyboardButton("💰 Payment Management", callback_data="payment")],
        [InlineKeyboardButton("📅 Subscription Management", callback_data="subscription")],
        [InlineKeyboardButton("✏️ Edit Applicant", callback_data="edit_applicant")],
        [InlineKeyboardButton("🗄️ Archive Management", callback_data="archive")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_view_menu() -> InlineKeyboardMarkup:
    """Get the view submenu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔍 Find Applicant", callback_data="find")],
        [InlineKeyboardButton("⏳ Pending Applicants", callback_data="view_pending")],
        [InlineKeyboardButton("✅ Done Applicants", callback_data="view_done")],
        [InlineKeyboardButton("📦 Archived Applicants", callback_data="view_archived")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payment_menu() -> InlineKeyboardMarkup:
    """Get the payment management keyboard."""
    keyboard = [
        [InlineKeyboardButton("✅ Mark as Done", callback_data="pay_done")],
        [InlineKeyboardButton("⏳ Mark as Pending", callback_data="pay_pending")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_subscription_menu() -> InlineKeyboardMarkup:
    """Get the subscription management keyboard."""
    keyboard = [
        [InlineKeyboardButton("📅 Set Subscription Date", callback_data="sub_set")],
        [InlineKeyboardButton("➕ Extend Subscription", callback_data="sub_extend")],
        [InlineKeyboardButton("❌ Expired", callback_data="sub_expired")],
        [InlineKeyboardButton("⏳ Expiring Soon", callback_data="sub_soon")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_archive_menu() -> InlineKeyboardMarkup:
    """Get the archive management keyboard."""
    keyboard = [
        [InlineKeyboardButton("📦 Archive Applicant", callback_data="arch_archive")],
        [InlineKeyboardButton("♻️ Restore Applicant", callback_data="arch_restore")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
    """Get a simple back button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=callback_data)]])


def get_cancel_button(callback_data: str = "back") -> InlineKeyboardMarkup:
    """Get a cancel button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data=callback_data)]])


def get_home_button() -> InlineKeyboardMarkup:
    """Get a home/main menu button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="back")]])


def get_editable_fields_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting editable fields."""
    keyboard = [
        [InlineKeyboardButton(v, callback_data=f"edit_col:{k}")]
        for k, v in EDITABLE_FIELDS.items()
    ]
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def get_application_plan_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting application plan."""
    keyboard = [
        [InlineKeyboardButton(plan, callback_data=f"plan:{plan}")]
        for plan in APPLICATION_PLAN_OPTIONS
    ]
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def get_boolean_keyboard(field_name: str) -> InlineKeyboardMarkup:
    """Get keyboard for boolean selection."""
    keyboard = [
        [InlineKeyboardButton("✅ True", callback_data=f"bool:true:{field_name}")],
        [InlineKeyboardButton("❌ False", callback_data=f"bool:false:{field_name}")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_proficiency_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for language proficiency selection."""
    keyboard = [
        [InlineKeyboardButton(prof, callback_data=f"prof:{prof}")]
        for prof in LANGUAGE_PROFICIENCY_OPTIONS
    ]
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def get_nested_field_menu(has_entries: bool, field_type: str) -> InlineKeyboardMarkup:
    """Get keyboard for nested field operations."""
    keyboard = [
        [InlineKeyboardButton("➕ Add New Entry", callback_data=f"nested_add:{field_type}")],
    ]
    
    if has_entries:
        keyboard.extend([
            [InlineKeyboardButton("✏️ Edit Entry", callback_data=f"nested_edit:{field_type}")],
            [InlineKeyboardButton("🗑️ Delete Entry", callback_data=f"nested_delete:{field_type}")],
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def get_entry_selection_keyboard(num_entries: int) -> InlineKeyboardMarkup:
    """Get keyboard for selecting an entry from a list."""
    keyboard = [
        [InlineKeyboardButton(f"Entry {i+1}", callback_data=f"entry_select:{i}")]
        for i in range(num_entries)
    ]
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)
