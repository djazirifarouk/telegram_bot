import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.keyboards.menus import (
    get_cancel_button,
    get_editable_fields_keyboard,
    get_application_plan_keyboard,
    get_nested_field_menu,
    get_entry_selection_keyboard,
    get_boolean_keyboard,
    get_proficiency_keyboard,
    get_home_button,
    get_yes_no_keyboard,
    get_employment_type_keyboard,
    get_search_accuracy_keyboard,
    get_currency_keyboard,
    get_socials_submenu_keyboard,
    get_general_submenu_keyboard,
    get_skills_menu_keyboard,
    get_recommendation_menu_keyboard,
    get_country_suggestions,
    get_countries_action_keyboard,
    get_continue_or_home_keyboard,
    get_back_button
)
from bot.formatters.display import format_nested_array
from bot.validators.input_validators import is_field_optional, get_field_prompt
from bot.handlers.skills_handler import handle_skills_menu
from database.queries import get_applicant, update_applicant
from utils.helpers import resolve_lookup
from utils.state_manager import state_manager
from config.settings import (
    EDITABLE_FIELDS,
    NESTED_FIELD_STRUCTURES,
    LANGUAGE_PROFICIENCY_OPTIONS
)

logger = logging.getLogger(__name__)


async def start_edit_applicant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start edit applicant flow."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state_manager.set_state(user_id, {
        "action": "edit_field",
        "step": "identify"
    })
    
    await query.message.edit_text(
        "✏️ *Edit Applicant*\n\n"
        "Send applicant **alias email** or **WhatsApp number**:",
        reply_markup=get_cancel_button("back"),
        parse_mode="Markdown"
    )


async def handle_edit_column_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle column selection for editing."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    col = query.data.split("edit_col:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    # REFRESH applicant data from database
    lookup_field = state.get("lookup_field")
    lookup_value = state.get("lookup_value")
    applicant = await get_applicant(lookup_field, lookup_value)
    
    if not applicant:
        await query.message.edit_text(
            "❌ Applicant not found.",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)
        return
    
    # Update state with fresh data
    state_manager.update_state(user_id, {"applicant": applicant})
    
    current_value = applicant.get(col)
    
    # Format current value for display
    if isinstance(current_value, list):
        current_display = ", ".join(str(v) for v in current_value) if current_value else "-"
    elif current_value is None:
        current_display = "-"
    else:
        current_display = str(current_value)
    
    state_manager.update_state(user_id, {
        "column": col,
        "current_value": current_value
    })
    
    # Handle different field types
    
    # Application Plan
    if col == "application_plan":
        state_manager.update_state(user_id, {"step": "menu_select"})
        await query.message.edit_text(
            f"📝 *Select Application Plan*\n\nCurrent: *{current_display}*",
            reply_markup=get_application_plan_keyboard(),
            parse_mode="Markdown"
        )
    
    # CV Upload
    elif col == "cv_url":
        state_manager.update_state(user_id, {"step": "upload_file", "file_type": "cv"})
        status = "Uploaded" if current_value else "Not uploaded"
        await query.message.edit_text(
            f"📄 *Upload New CV*\n\nCurrent Status: {status}\n\n"
            "Please send the CV file (PDF, DOC, DOCX).\n\n"
            "Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    # Profile Picture Upload
    elif col == "picture_url":
        state_manager.update_state(user_id, {"step": "upload_file", "file_type": "picture"})
        status = "Uploaded" if current_value else "Not uploaded"
        await query.message.edit_text(
            f"📸 *Upload New Profile Picture*\n\nCurrent Status: {status}\n\n"
            "Please send the profile picture (JPG, PNG).\n\n"
            "Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    # Recommendation Letters (Array of URLs)
    elif col == "recommendation_url":
        state_manager.update_state(user_id, {"step": "submenu"})
        
        # Parse if stored as string
        current_value_raw = current_value
        if isinstance(current_value_raw, str):
            try:
                import json
                current_value = json.loads(current_value_raw) if current_value_raw else []
            except:
                current_value = []
        
        letters_count = len(current_value) if current_value else 0
        await query.message.edit_text(
            f"📝 *Recommendation Letters*\n\nCurrent: {letters_count} letter(s)\n\n"
            "Select an action:",
            reply_markup=get_recommendation_menu_keyboard(),
            parse_mode="Markdown"
        )
    
    # Achievements (Text field)
    elif col == "achievements":
        state_manager.update_state(user_id, {"step": "text_input"})
        await query.message.edit_text(
            f"🏆 *Achievements*\n\nCurrent: {current_display}\n\n"
            "Enter new achievements:\n\n"
            "Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    # Authorized Countries (Multiple choice)
    elif col == "authorized_countries" or col == "country_preference":
        state_manager.update_state(user_id, {"step": "submenu"})
        
        current_list = current_value if isinstance(current_value, list) else []
        count = len(current_list)
        current_text = ", ".join(current_list) if current_list else "-"
        
        from bot.keyboards.menus import get_countries_action_keyboard
        await query.message.edit_text(
            f"🌍 *{EDITABLE_FIELDS[col]}*\n\n"
            f"Current ({count}): {current_text}\n\n"
            "Select an action:",
            reply_markup=get_countries_action_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Visa (Yes/No)
    elif col == "visa":
        state_manager.update_state(user_id, {"step": "menu_select"})
        await query.message.edit_text(
            f"🛂 *Visa Status*\n\nCurrent: {current_display}\n\n"
            "Do you have a visa?",
            reply_markup=get_yes_no_keyboard("visa"),
            parse_mode="Markdown"
        )
    
    # Relocate (Yes/No)
    elif col == "relocate":
        state_manager.update_state(user_id, {"step": "menu_select"})
        await query.message.edit_text(
            f"✈️ *Willing to Relocate*\n\nCurrent: {current_display}\n\n"
            "Are you willing to relocate?",
            reply_markup=get_yes_no_keyboard("relocate"),
            parse_mode="Markdown"
        )
    
    # Experience (Number 0-50)
    elif col == "experience":
        state_manager.update_state(user_id, {"step": "number_input", "min": 0, "max": 50})
        await query.message.edit_text(
            f"💼 *Years of Experience*\n\nCurrent: {current_display}\n\n"
            "Enter years of experience (0-50):\n\n"
            "Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    # Employment Type
    elif col == "employment_type":
        state_manager.update_state(user_id, {"step": "menu_select"})
        await query.message.edit_text(
            f"💼 *Employment Type*\n\nCurrent: {current_display}\n\n"
            "Select employment type:",
            reply_markup=get_employment_type_keyboard(),
            parse_mode="Markdown"
        )
    
    # Search Accuracy
    elif col == "search_accuracy":
        state_manager.update_state(user_id, {"step": "menu_select"})
        await query.message.edit_text(
            f"🎯 *Search Accuracy*\n\nCurrent: {current_display}\n\n"
            "Select search accuracy:",
            reply_markup=get_search_accuracy_keyboard(),
            parse_mode="Markdown"
        )
    
    # Country Preference (Multiple choice)
    elif col == "country_preference":
        state_manager.update_state(user_id, {"step": "country_select", "selected_countries": []})
        await query.message.edit_text(
            f"🌍 *Country Preferences*\n\nCurrent: {current_display}\n\n"
            "Type a country name to see suggestions.\n"
            "You can add multiple countries.\n\n"
            "Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    # Socials (Submenu)
    elif col == "socials":
        state_manager.update_state(user_id, {"step": "submenu"})
        await query.message.edit_text(
            f"🔗 *Social Media Links*\n\n"
            f"LinkedIn: {applicant.get('linkedin', '-')}\n"
            f"Twitter: {applicant.get('twitter', '-')}\n"
            f"Website: {applicant.get('website', '-')}\n"
            f"GitHub: {applicant.get('github', '-')}\n\n"
            "Select which to edit:",
            reply_markup=get_socials_submenu_keyboard(),
            parse_mode="Markdown"
        )
    
    # Apply Role (Text)
    elif col == "apply_role":
        state_manager.update_state(user_id, {"step": "text_input"})
        await query.message.edit_text(
            f"💼 *Applying For Role*\n\nCurrent: {current_display}\n\n"
            "Enter the role you're applying for:\n\n"
            "Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    # General (Submenu)
    elif col == "general":
        state_manager.update_state(user_id, {"step": "submenu"})
        await query.message.edit_text(
            f"📊 *General Information*\n\n"
            f"Current Salary: {applicant.get('current_salary', '-')}\n"
            f"Notice Period: {applicant.get('notice_period', '-')} days\n"
            f"Expected Salary: {applicant.get('expected_salary', '-')} {applicant.get('expected_salary_currency', '')}\n\n"
            "Select what to edit:",
            reply_markup=get_general_submenu_keyboard(),
            parse_mode="Markdown"
        )
    
    # Skills (Array management)
    elif col == "skills":
        state_manager.update_state(user_id, {"step": "submenu"})
        skills_count = len(current_value) if current_value else 0
        await query.message.edit_text(
            f"🎯 *Skills*\n\nCurrent: {skills_count} skill(s)\n{current_display}\n\n"
            "Select an action:",
            reply_markup=get_skills_menu_keyboard(),
            parse_mode="Markdown"
        )
    
    # Nested fields (roles, education, etc.)
    elif col in NESTED_FIELD_STRUCTURES:
        state_manager.update_state(user_id, {"step": "nested_menu"})
        current_data = applicant.get(col, [])
        has_entries = current_data and len(current_data) > 0
        
        if has_entries:
            await query.message.edit_text(
                f"📋 *Current {EDITABLE_FIELDS[col]}:*\n{format_nested_array(current_data, col)}\n\n"
                "Select an action:",
                reply_markup=get_nested_field_menu(has_entries, col),
                parse_mode="Markdown"
            )
        else:
            await query.message.edit_text(
                f"📋 *{EDITABLE_FIELDS[col]}*\n\nNo entries found. Add a new one?",
                reply_markup=get_nested_field_menu(has_entries, col),
                parse_mode="Markdown"
            )
    
    # Simple text fields
    else:
        state_manager.update_state(user_id, {"step": "text_input"})
        await query.message.edit_text(
            f"✏️ *Editing {EDITABLE_FIELDS[col]}*\n\nCurrent: {current_display}\n\n"
            "Send the new value:\n\n"
            "Send /cancel to abort.",
            parse_mode="Markdown"
        )


async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle application plan selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    plan = query.data.split("plan:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    lookup_field = state["lookup_field"]
    lookup_value = state["lookup_value"]
    
    success = await update_applicant(lookup_field, lookup_value, {"application_plan": plan})
    
    if success:
        await query.message.edit_text(
            f"✅ *Application Plan updated to: {plan}*",
            reply_markup=get_continue_or_home_keyboard(),
            parse_mode="Markdown"
        )
        # DON'T clear state - keep it for continue editing
    else:
        await query.message.edit_text(
            "❌ Error updating application plan",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)




# ==================== NESTED FIELD HANDLERS ====================

async def handle_nested_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle adding new entry to nested field."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    field_type = query.data.split("nested_add:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    state_manager.update_state(user_id, {
        "step": "nested_input",
        "nested_action": "add",
        "nested_type": field_type,
        "nested_data": {},
        "nested_field_index": 0
    })
    
    # Start collecting fields
    structure = NESTED_FIELD_STRUCTURES[field_type]
    first_field = structure["fields"][0]
    field_label = structure["labels"][first_field]
    field_types = structure.get("types", {})
    
    # Check if it's a boolean or select field
    if first_field in field_types:
        if field_types[first_field] == "boolean":
            await query.message.edit_text(
                f"Select *{field_label}*:",
                reply_markup=get_boolean_keyboard(first_field),
                parse_mode="Markdown"
            )
            return
        elif field_types[first_field] == "select" and first_field == "proficiency":
            await query.message.edit_text(
                f"Select *{field_label}*:",
                reply_markup=get_proficiency_keyboard(),
                parse_mode="Markdown"
            )
            return
    
    # Text field with optional skip
    optional_text = ""
    if is_field_optional(field_type, first_field):
        optional_text = "\n\n💡 _Send 'skip' or 'empty' to leave blank_"
    
    await query.message.edit_text(
        f"📝 Enter *{field_label}*:{optional_text}",
        parse_mode="Markdown"
    )


async def handle_nested_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle editing existing entry in nested field."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    field_type = query.data.split("nested_edit:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    applicant = state.get("applicant", {})
    current_data = applicant.get(field_type, [])
    
    if not current_data or len(current_data) == 0:
        await query.message.edit_text("❌ No entries to edit.")
        return
    
    state_manager.update_state(user_id, {
        "step": "nested_select_entry",
        "nested_action": "edit",
        "nested_type": field_type
    })
    
    await query.message.edit_text(
        f"✏️ *Select entry to edit:*\n{format_nested_array(current_data, field_type)}",
        reply_markup=get_entry_selection_keyboard(len(current_data)),
        parse_mode="Markdown"
    )


async def handle_nested_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deleting entry from nested field."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    field_type = query.data.split("nested_delete:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    applicant = state.get("applicant", {})
    current_data = applicant.get(field_type, [])
    
    if not current_data or len(current_data) == 0:
        await query.message.edit_text("❌ No entries to delete.")
        return
    
    state_manager.update_state(user_id, {
        "step": "nested_select_entry",
        "nested_action": "delete",
        "nested_type": field_type
    })
    
    await query.message.edit_text(
        f"🗑️ *Select entry to delete:*\n{format_nested_array(current_data, field_type)}",
        reply_markup=get_entry_selection_keyboard(len(current_data)),
        parse_mode="Markdown"
    )


async def handle_entry_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle entry selection for edit/delete."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    entry_index = int(query.data.split("entry_select:")[1])
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    nested_action = state.get("nested_action")
    field_type = state.get("nested_type")
    applicant = state.get("applicant", {})
    current_data = applicant.get(field_type, [])
    
    if entry_index >= len(current_data):
        await query.message.edit_text("❌ Invalid entry selection.")
        return
    
    # DELETE ACTION
    if nested_action == "delete":
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]
        
        deleted_entry = current_data.pop(entry_index)
        
        success = await update_applicant(lookup_field, lookup_value, {field_type: current_data})
        
        if success:
            await query.message.edit_text(
                f"✅ *Entry {entry_index + 1} deleted successfully!*\n\n"
                f"Deleted: {str(deleted_entry)[:100]}...",
                reply_markup=get_continue_or_home_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.message.edit_text(
                "❌ Error deleting entry",
                reply_markup=get_continue_or_home_keyboard()
            )
        
        state_manager.clear_state(user_id)
    
    # EDIT ACTION
    elif nested_action == "edit":
        state_manager.update_state(user_id, {
            "step": "nested_input",
            "nested_entry_index": entry_index,
            "nested_data": current_data[entry_index].copy(),
            "nested_field_index": 0
        })
        
        structure = NESTED_FIELD_STRUCTURES[field_type]
        first_field = structure["fields"][0]
        field_label = structure["labels"][first_field]
        current_value = current_data[entry_index].get(first_field, "")
        field_types = structure.get("types", {})
        
        # Check if it's a boolean or select field
        if first_field in field_types:
            if field_types[first_field] == "boolean":
                await query.message.edit_text(
                    f"Current: *{current_value}*\n\nSelect new *{field_label}*:",
                    reply_markup=get_boolean_keyboard(first_field),
                    parse_mode="Markdown"
                )
                return
            elif field_types[first_field] == "select" and first_field == "proficiency":
                await query.message.edit_text(
                    f"Current: *{current_value}*\n\nSelect new *{field_label}*:",
                    reply_markup=get_proficiency_keyboard(),
                    parse_mode="Markdown"
                )
                return
        
        optional_text = ""
        if is_field_optional(field_type, first_field):
            optional_text = "\n\n💡 _Send 'skip' or 'empty' to leave blank_"
        
        await query.message.edit_text(
            f"Current: *{current_value}*\n\nEnter new *{field_label}*:{optional_text}",
            parse_mode="Markdown"
        )


async def handle_boolean_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle boolean field selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    _, value, field_name = query.data.split(":", 2)
    bool_value = value == "true"
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    # Import here to avoid circular import
    from bot.handlers.text_handler import process_nested_field_input
    
    # Pass the boolean value as string and let it be processed
    await process_nested_field_input(update, str(bool_value), state)


async def handle_proficiency_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle proficiency level selection."""
    query = update.callback_query
    await query.answer()
    
    proficiency = query.data.split("prof:", 1)[1]
    
    # Import here to avoid circular import
    from bot.handlers.text_handler import process_nested_field_input
    
    await process_nested_field_input(update, proficiency, state_manager.get_state(query.from_user.id))

async def handle_yesno_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Yes/No selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    _, value, field_name = query.data.split(":", 2)
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    lookup_field = state["lookup_field"]
    lookup_value = state["lookup_value"]
    
    success = await update_applicant(lookup_field, lookup_value, {field_name: value.capitalize()})
    
    if success:
        await query.message.edit_text(
            f"✅ *{EDITABLE_FIELDS[field_name]} updated to: {value.capitalize()}*",
            reply_markup=get_continue_or_home_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await query.message.edit_text(
            "❌ Error updating field",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)
async def handle_employment_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle employment type selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    emp_type = query.data.split("emptype:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    lookup_field = state["lookup_field"]
    lookup_value = state["lookup_value"]
    
    success = await update_applicant(lookup_field, lookup_value, {"employment_type": emp_type})
    
    if success:
        await query.message.edit_text(
            f"✅ *Employment Type updated to: {emp_type}*",
            reply_markup=get_continue_or_home_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await query.message.edit_text(
            "❌ Error updating field",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)


async def handle_search_accuracy_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search accuracy selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    accuracy = query.data.split("accuracy:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    lookup_field = state["lookup_field"]
    lookup_value = state["lookup_value"]
    
    success = await update_applicant(lookup_field, lookup_value, {"search_accuracy": accuracy})
    
    if success:
        await query.message.edit_text(
            f"✅ *Search Accuracy updated to: {accuracy}*",
            reply_markup=get_continue_or_home_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await query.message.edit_text(
            "❌ Error updating field",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)


async def handle_currency_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle currency selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    currency = query.data.split("currency:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    lookup_field = state["lookup_field"]
    lookup_value = state["lookup_value"]
    
    success = await update_applicant(lookup_field, lookup_value, {"expected_salary_currency": currency})
    
    if success:
        await query.message.edit_text(
            f"✅ *Salary Currency updated to: {currency}*",
            reply_markup=get_continue_or_home_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await query.message.edit_text(
            "❌ Error updating field",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)


async def handle_back_to_fields(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to field selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state = state_manager.get_state(user_id)
    
    if not state:
        return
    
    # Reset to field selection
    state_manager.update_state(user_id, {"step": "choose_field"})
    
    await query.message.edit_text(
        "🧩 *Select field to edit:*",
        reply_markup=get_editable_fields_keyboard(),
        parse_mode="Markdown"
    )


async def handle_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country selection from suggestions."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Handle remove action
    if query.data.startswith("country_rm:"):
        country = query.data.split("country_rm:", 1)[1]
        state = state_manager.get_state(user_id)
        if not state:
            return
        
        selected = state.get("selected_countries", [])
        if country in selected:
            selected.remove(country)
        else:
            selected.append(country)
        
        state_manager.update_state(user_id, {"selected_countries": selected})
        
        # Show updated selection
        selected_text = f"Selected for removal: {', '.join(selected)}" if selected else "None selected"
        applicant = state.get("applicant", {})
        col = state.get("column")
        current_countries = applicant.get(col, [])
        
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [
            [InlineKeyboardButton(f"{'✅ ' if c in selected else ''}{c}", callback_data=f"country_rm:{c}")]
            for c in current_countries
        ]
        keyboard.append([InlineKeyboardButton("✅ Done Removing", callback_data="country:done")])
        keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back_to_fields")])
        
        await query.message.edit_text(
            f"🗑️ *Remove Countries*\n\n{selected_text}\n\nSelect more to remove:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    # Handle regular selection
    data = query.data.split("country:", 1)[1]
    state = state_manager.get_state(user_id)
    if not state:
        logger.error("No state found in handle_country_selection")
        return
    
    if data == "done":
        col = state.get("column")
        selected_countries = state.get("selected_countries", [])
        lookup_field = state.get("lookup_field")
        lookup_value = state.get("lookup_value")
        action_type = state.get("action_type", "add")
        
        logger.info(f"Saving countries - Column: {col}, Action: {action_type}, Selected: {selected_countries}")
        
        # Get FRESH current countries from database (don't trust state)
        applicant = await get_applicant(lookup_field, lookup_value)
        if not applicant:
            await query.message.edit_text("❌ Applicant not found.")
            state_manager.clear_state(user_id)
            return
        
        current_countries = applicant.get(col, [])
        if not isinstance(current_countries, list):
            current_countries = []
        
        logger.info(f"Current countries in DB: {current_countries}")
        
        # Add or remove
        if action_type == "add":
            for country in selected_countries:
                if country not in current_countries:
                    current_countries.append(country)
            action_text = "added"
        else:  # remove
            for country in selected_countries:
                if country in current_countries:
                    current_countries.remove(country)
            action_text = "removed"
        
        logger.info(f"New countries list: {current_countries}")
        
        if not selected_countries:
            from bot.keyboards.menus import get_back_button
            await query.message.edit_text(
                f"❌ No countries selected to {action_type}.",
                reply_markup=get_back_button("back_to_fields")
            )
            return
        
        # Update database
        logger.info(f"Updating database - Field: {col}, Value: {current_countries}")
        success = await update_applicant(lookup_field, lookup_value, {col: current_countries})
        
        if success:
            logger.info(f"Database update successful!")
            
            # Verify the update
            verify_applicant = await get_applicant(lookup_field, lookup_value)
            verify_countries = verify_applicant.get(col, [])
            logger.info(f"Verification - Countries after update: {verify_countries}")
            
            changes = ", ".join(selected_countries)
            from bot.keyboards.menus import get_continue_or_home_keyboard
            await query.message.edit_text(
                f"✅ *Countries {action_text}!*\n\n"
                f"{changes}\n\n"
                f"Total: {len(current_countries)} countries",
                reply_markup=get_continue_or_home_keyboard(),
                parse_mode="Markdown"
            )
            
            # Refresh applicant data in state
            state_manager.update_state(user_id, {"applicant": verify_applicant})
        else:
            logger.error(f"Database update FAILED!")
            from bot.keyboards.menus import get_home_button
            await query.message.edit_text(
                "❌ Error updating countries. Check logs for details.",
                reply_markup=get_home_button()
            )
            state_manager.clear_state(user_id)
    else:
        # Add country to selection
        selected_countries = state.get("selected_countries", [])
        if data not in selected_countries:
            selected_countries.append(data)
            state_manager.update_state(user_id, {"selected_countries": selected_countries})
        
        selected_text = ", ".join(selected_countries)
        
        logger.info(f"Country added to selection: {data}. Total selected: {selected_countries}")
        
        # Show message to continue typing or click done
        await query.message.edit_text(
            f"✅ *Added to selection: {data}*\n\n"
            f"Currently selected: {selected_text}\n\n"
            f"Type another country name to add more, or click the button below.",
            parse_mode="Markdown"
        )
        
        # Send new message with done button
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [
            [InlineKeyboardButton("✅ Done Adding", callback_data="country:done")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="back_to_fields")]
        ]
        await query.message.reply_text(
            "Continue?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_countries_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle countries add/remove/view actions."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action = query.data.split("countries:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    applicant = state.get("applicant", {})
    col = state.get("column")
    current_countries = applicant.get(col, [])
    if not isinstance(current_countries, list):
        current_countries = []
    
    if action == "add":
        state_manager.update_state(user_id, {
            "step": "country_select",
            "selected_countries": [],
            "action_type": "add"
        })
        
        current_text = ", ".join(current_countries) if current_countries else "-"
        
        await query.message.edit_text(
            f"➕ *Add Countries*\n\n"
            f"Current ({len(current_countries)}): {current_text}\n\n"
            f"Type a country name (e.g., 'tun' for Tunisia)\n"
            f"You'll see suggestions to choose from.\n\n"
            f"Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    elif action == "remove":
        if not current_countries:
            from bot.keyboards.menus import get_back_button
            await query.message.edit_text(
                "❌ No countries to remove.",
                reply_markup=get_back_button("back_to_fields")
            )
            return
        
        state_manager.update_state(user_id, {
            "step": "country_select",
            "selected_countries": [],
            "action_type": "remove"
        })
        
        # Create keyboard with current countries
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [
            [InlineKeyboardButton(country, callback_data=f"country_rm:{country}")]
            for country in current_countries
        ]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="country:done")])
        keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back_to_fields")])
        
        await query.message.edit_text(
            f"🗑️ *Remove Countries*\n\n"
            f"Select countries to remove:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif action == "view":
        if not current_countries:
            countries_display = "-"
        else:
            countries_display = "\n".join([f"• {c}" for c in current_countries])
        
        from bot.keyboards.menus import get_back_button
        await query.message.edit_text(
            f"📋 *Current Countries ({len(current_countries)})*\n\n{countries_display}",
            reply_markup=get_back_button("back_to_fields"),
            parse_mode="Markdown"
        )


async def handle_social_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle social media field selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    social_field = query.data.split("social:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    applicant = state.get("applicant", {})
    current_value = applicant.get(social_field, "")
    
    # Map to friendly names
    field_names = {
        "linkedin": "LinkedIn",
        "twitter": "Twitter/X",
        "website": "Website/Portfolio",
        "github": "GitHub"
    }
    
    state_manager.update_state(user_id, {
        "step": "text_input",
        "column": social_field  # Store the actual field name
    })
    
    await query.message.edit_text(
        f"🔗 *{field_names.get(social_field, social_field)}*\n\n"
        f"Current: {current_value if current_value else 'Not set'}\n\n"
        f"Send the new URL:\n\n"
        f"Send /cancel to abort.",
        parse_mode="Markdown"
    )


async def handle_general_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle general information field selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    field = query.data.split("general:")[1]
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    applicant = state.get("applicant", {})
    current_value = applicant.get(field, "")
    
    state_manager.update_state(user_id, {"column": field})
    
    # Handle currency selection with menu
    if field == "expected_salary_currency":
        state_manager.update_state(user_id, {"step": "menu_select"})
        await query.message.edit_text(
            f"💱 *Salary Currency*\n\nCurrent: {current_value if current_value else 'Not set'}\n\n"
            "Select currency:",
            reply_markup=get_currency_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # Numeric fields
        state_manager.update_state(user_id, {"step": "number_input", "min": 0, "max": 999999})
        
        field_names = {
            "current_salary": "Current Salary",
            "notice_period": "Notice Period (days)",
            "expected_salary": "Expected Salary"
        }
        
        await query.message.edit_text(
            f"💵 *{field_names.get(field, field)}*\n\n"
            f"Current: {current_value if current_value else 'Not set'}\n\n"
            f"Enter the new value:\n\n"
            f"Send /cancel to abort.",
            parse_mode="Markdown"
        )


async def handle_continue_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow user to continue editing the same applicant."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state = state_manager.get_state(user_id)
    
    if not state:
        await query.message.edit_text(
            "❌ Session expired. Please start again.",
            reply_markup=get_home_button()
        )
        return
    
    # IMPORTANT: Refresh applicant data from database
    lookup_field = state.get("lookup_field")
    lookup_value = state.get("lookup_value")
    
    # Get fresh data from database
    applicant = await get_applicant(lookup_field, lookup_value)
    if not applicant:
        await query.message.edit_text(
            "❌ Applicant not found.",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)
        return
    
    # Update state with fresh data
    state_manager.update_state(user_id, {
        "step": "choose_field",
        "applicant": applicant  # Fresh data from DB
    })
    
    name = f"{applicant.get('first_name', '')} {applicant.get('last_name', '')}"
    
    await query.message.edit_text(
        f"✏️ *Continue Editing: {name}*\n\nSelect field to edit:",
        reply_markup=get_editable_fields_keyboard(),
        parse_mode="Markdown"
    )


async def handle_recommendation_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle recommendation letters menu selection."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split("rec:")[1]
    user_id = query.from_user.id
    state = state_manager.get_state(user_id)
    
    if not state:
        return
    
    applicant = state.get("applicant", {})
    
    # Parse recommendation_url if it's a string
    import json
    current_letters_raw = applicant.get("recommendation_url", [])
    
    if isinstance(current_letters_raw, str):
        try:
            current_letters = json.loads(current_letters_raw) if current_letters_raw else []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse recommendation_url: {current_letters_raw}")
            current_letters = []
    else:
        current_letters = current_letters_raw if isinstance(current_letters_raw, list) else []
    
    if action == "add":
        state_manager.update_state(user_id, {"step": "upload_file", "file_type": "recommendation"})
        await query.message.edit_text(
            f"📝 *Add Recommendation Letter*\n\n"
            f"Current: {len(current_letters)} letter(s)\n\n"
            f"Please upload the recommendation letter (PDF).\n\n"
            f"Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    elif action == "remove":
        if not current_letters:
            from bot.keyboards.menus import get_back_button
            await query.message.edit_text(
                "❌ No letters to remove.",
                reply_markup=get_back_button("back_to_fields")
            )
            return
        
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [
            [InlineKeyboardButton(f"Letter {i+1}", callback_data=f"rec_rm:{i}")]
            for i in range(len(current_letters))
        ]
        keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back_to_fields")])
        
        await query.message.edit_text(
            f"🗑️ *Remove Recommendation Letter*\n\n"
            f"Total: {len(current_letters)} letter(s)\n\n"
            f"Select letter to remove:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif action == "view":
        if not current_letters:
            letters_display = "None"
        else:
            # DON'T use Markdown when displaying URLs - use plain text
            letters_list = []
            for i, url in enumerate(current_letters, 1):
                # Extract just the filename from the URL
                filename = url.split('/')[-1]
                letters_list.append(f"{i}. {filename}")
            letters_display = "\n".join(letters_list)
        
        from bot.keyboards.menus import get_back_button
        # Use parse_mode=None to avoid Markdown parsing errors
        await query.message.edit_text(
            f"📋 Recommendation Letters ({len(current_letters)})\n\n{letters_display}",
            reply_markup=get_back_button("back_to_fields"),
            parse_mode=None  # Changed from 'Markdown' to None
        )

async def handle_recommendation_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle removing a recommendation letter."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    letter_index = int(query.data.split("rec_rm:")[1])
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    lookup_field = state["lookup_field"]
    lookup_value = state["lookup_value"]
    
    applicant = await get_applicant(lookup_field, lookup_value)
    current_letters = applicant.get("recommendation_url", [])
    
    if letter_index >= len(current_letters):
        await query.message.edit_text("❌ Invalid selection.")
        return
    
    removed_url = current_letters.pop(letter_index)
    
    from database.queries import delete_file_from_storage
    await delete_file_from_storage(removed_url, "letters")
    
    success = await update_applicant(lookup_field, lookup_value, {"recommendation_url": current_letters})
    
    if success:
        from bot.keyboards.menus import get_continue_or_home_keyboard
        await query.message.edit_text(
            f"✅ *Letter removed successfully!*\n\n"
            f"Remaining: {len(current_letters)} letter(s)",
            reply_markup=get_continue_or_home_keyboard(),
            parse_mode="Markdown"
        )
        applicant = await get_applicant(lookup_field, lookup_value)
        state_manager.update_state(user_id, {"applicant": applicant})
    else:
        from bot.keyboards.menus import get_home_button
        await query.message.edit_text(
            "❌ Error removing letter",
            reply_markup=get_home_button()
        )


# Register all new handlers
def register_edit_handlers(application):
    """Register edit-related handlers - COMPLETE VERSION."""
    
    # Main edit handlers
    application.add_handler(CallbackQueryHandler(start_edit_applicant, pattern="^edit_applicant$"))
    application.add_handler(CallbackQueryHandler(handle_edit_column_selection, pattern="^edit_col:"))
    
    # Menu selections
    application.add_handler(CallbackQueryHandler(handle_plan_selection, pattern="^plan:"))
    application.add_handler(CallbackQueryHandler(handle_yesno_selection, pattern="^yesno:"))
    application.add_handler(CallbackQueryHandler(handle_employment_type_selection, pattern="^emptype:"))
    application.add_handler(CallbackQueryHandler(handle_search_accuracy_selection, pattern="^accuracy:"))
    application.add_handler(CallbackQueryHandler(handle_currency_selection, pattern="^currency:"))
    
    # Submenu handlers - THESE WERE MISSING!
    application.add_handler(CallbackQueryHandler(handle_social_selection, pattern="^social:"))
    application.add_handler(CallbackQueryHandler(handle_general_selection, pattern="^general:"))
    application.add_handler(CallbackQueryHandler(handle_countries_action, pattern="^countries:"))
    application.add_handler(CallbackQueryHandler(handle_skills_menu, pattern="^skills:"))
    
    # Navigation
    application.add_handler(CallbackQueryHandler(handle_back_to_fields, pattern="^back_to_fields$"))
    application.add_handler(CallbackQueryHandler(handle_continue_edit, pattern="^continue_edit$"))
    application.add_handler(CallbackQueryHandler(handle_recommendation_menu, pattern="^rec:"))
    application.add_handler(CallbackQueryHandler(handle_recommendation_remove, pattern="^rec_rm:"))
    
    # Country selection (must be AFTER countries_action to avoid conflicts)
    application.add_handler(CallbackQueryHandler(handle_country_selection, pattern="^country"))
    
    # Nested field handlers
    application.add_handler(CallbackQueryHandler(handle_nested_add, pattern="^nested_add:"))
    application.add_handler(CallbackQueryHandler(handle_nested_edit, pattern="^nested_edit:"))
    application.add_handler(CallbackQueryHandler(handle_nested_delete, pattern="^nested_delete:"))
    application.add_handler(CallbackQueryHandler(handle_entry_selection, pattern="^entry_select:"))
    application.add_handler(CallbackQueryHandler(handle_boolean_selection, pattern="^bool:"))
    application.add_handler(CallbackQueryHandler(handle_proficiency_selection, pattern="^prof:"))

