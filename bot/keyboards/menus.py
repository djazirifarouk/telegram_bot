from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.settings import (
    EDITABLE_FIELDS,
    APPLICATION_PLAN_OPTIONS,
    LANGUAGE_PROFICIENCY_OPTIONS,
    EMPLOYMENT_TYPE_OPTIONS,
    SEARCH_ACCURACY_OPTIONS,
    CURRENCY_OPTIONS,
    COUNTRIES_LIST  # ADD THIS to config/settings.py
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

def get_yes_no_keyboard(field_name: str) -> InlineKeyboardMarkup:
    """Get Yes/No keyboard."""
    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data=f"yesno:yes:{field_name}")],
        [InlineKeyboardButton("❌ No", callback_data=f"yesno:no:{field_name}")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_employment_type_keyboard() -> InlineKeyboardMarkup:
    """Get employment type keyboard."""
    keyboard = [
        [InlineKeyboardButton(emp_type, callback_data=f"emptype:{emp_type}")]
        for emp_type in EMPLOYMENT_TYPE_OPTIONS
    ]
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def get_search_accuracy_keyboard() -> InlineKeyboardMarkup:
    """Get search accuracy keyboard."""
    keyboard = [
        [InlineKeyboardButton(accuracy, callback_data=f"accuracy:{accuracy}")]
        for accuracy in SEARCH_ACCURACY_OPTIONS
    ]
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def get_currency_keyboard() -> InlineKeyboardMarkup:
    """Get currency keyboard."""
    keyboard = [
        [InlineKeyboardButton(currency, callback_data=f"currency:{currency}")]
        for currency in CURRENCY_OPTIONS
    ]
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def get_socials_submenu_keyboard() -> InlineKeyboardMarkup:
    """Get social media submenu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔗 LinkedIn", callback_data="social:linkedin")],
        [InlineKeyboardButton("🐦 Twitter/X", callback_data="social:twitter")],
        [InlineKeyboardButton("🌐 Website/Portfolio", callback_data="social:website")],
        [InlineKeyboardButton("💻 GitHub", callback_data="social:github")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_fields")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_general_submenu_keyboard() -> InlineKeyboardMarkup:
    """Get general information submenu keyboard."""
    keyboard = [
        [InlineKeyboardButton("💵 Current Salary", callback_data="general:current_salary")],
        [InlineKeyboardButton("⏰ Notice Period (days)", callback_data="general:notice_period")],
        [InlineKeyboardButton("💰 Expected Salary", callback_data="general:expected_salary")],
        [InlineKeyboardButton("💱 Salary Currency", callback_data="general:expected_salary_currency")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_fields")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_skills_menu_keyboard() -> InlineKeyboardMarkup:
    """Get skills management keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Skills", callback_data="skills:add")],
        [InlineKeyboardButton("🗑️ Remove Skills", callback_data="skills:remove")],
        [InlineKeyboardButton("📋 View All Skills", callback_data="skills:view")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_fields")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_recommendation_menu_keyboard() -> InlineKeyboardMarkup:
    """Get recommendation letters management keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Letter", callback_data="rec:add")],
        [InlineKeyboardButton("🗑️ Remove Letter", callback_data="rec:remove")],
        [InlineKeyboardButton("📋 View All Letters", callback_data="rec:view")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_fields")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_countries_action_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for countries management actions."""
    keyboard = [
        [InlineKeyboardButton("➕ Add Countries", callback_data="countries:add")],
        [InlineKeyboardButton("🗑️ Remove Countries", callback_data="countries:remove")],
        [InlineKeyboardButton("📋 View Current", callback_data="countries:view")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_fields")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_country_suggestions(typed_text: str, max_suggestions: int = 5) -> InlineKeyboardMarkup:
    """Get country suggestions based on typed text."""
    from config.settings import COUNTRIES_LIST
    
    # Filter countries that start with typed text (case-insensitive)
    suggestions = [
        country for country in COUNTRIES_LIST
        if country.lower().startswith(typed_text.lower())
    ][:max_suggestions]
    
    keyboard = [
        [InlineKeyboardButton(country, callback_data=f"country:{country}")]
        for country in suggestions
    ]
    
    # Add options
    keyboard.append([InlineKeyboardButton("✅ Done Adding", callback_data="country:done")])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
    
    return InlineKeyboardMarkup(keyboard)


def get_continue_or_home_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard to continue editing or go home."""
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Another Field", callback_data="continue_edit")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)
