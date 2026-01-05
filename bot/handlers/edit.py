import logging
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.keyboards.menus import (
    get_cancel_button,
    get_editable_fields_keyboard,
    get_application_plan_keyboard,
    get_nested_field_menu,
    get_entry_selection_keyboard,
    get_boolean_keyboard,
    get_proficiency_keyboard,
    get_home_button
)
from bot.formatters.display import format_nested_array
from bot.validators.input_validators import is_field_optional, get_field_prompt
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
    
    state_manager.update_state(user_id, {
        "step": "nested_menu" if col in NESTED_FIELD_STRUCTURES else "edit_value",
        "column": col
    })
    
    # Handle application_plan with menu
    if col == "application_plan":
        await query.message.edit_text(
            "📝 *Select Application Plan:*",
            reply_markup=get_application_plan_keyboard(),
            parse_mode="Markdown"
        )
    # Handle nested fields
    elif col in NESTED_FIELD_STRUCTURES:
        applicant = state.get("applicant", {})
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
    # Handle simple text fields
    else:
        await query.message.edit_text(
            f"✏️ *Editing {EDITABLE_FIELDS[col]}*\n\nSend the new value:",
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
            reply_markup=get_home_button(),
            parse_mode="Markdown"
        )
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
                reply_markup=get_home_button(),
                parse_mode="Markdown"
            )
        else:
            await query.message.edit_text(
                "❌ Error deleting entry",
                reply_markup=get_home_button()
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
    
    _, value, field_name = query.data.split(":", 2)
    bool_value = value == "true"
    
    # Import here to avoid circular import
    from bot.handlers.text_handler import process_nested_field_input
    
    await process_nested_field_input(update, str(bool_value), state_manager.get_state(query.from_user.id))


async def handle_proficiency_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle proficiency level selection."""
    query = update.callback_query
    await query.answer()
    
    proficiency = query.data.split("prof:", 1)[1]
    
    # Import here to avoid circular import
    from bot.handlers.text_handler import process_nested_field_input
    
    await process_nested_field_input(update, proficiency, state_manager.get_state(query.from_user.id))


def register_edit_handlers(application):
    """Register edit-related handlers."""
    application.add_handler(CallbackQueryHandler(start_edit_applicant, pattern="^edit_applicant$"))
    application.add_handler(CallbackQueryHandler(handle_edit_column_selection, pattern="^edit_col:"))
    application.add_handler(CallbackQueryHandler(handle_plan_selection, pattern="^plan:"))
    
    # Nested field handlers
    application.add_handler(CallbackQueryHandler(handle_nested_add, pattern="^nested_add:"))
    application.add_handler(CallbackQueryHandler(handle_nested_edit, pattern="^nested_edit:"))
    application.add_handler(CallbackQueryHandler(handle_nested_delete, pattern="^nested_delete:"))
    application.add_handler(CallbackQueryHandler(handle_entry_selection, pattern="^entry_select:"))
    application.add_handler(CallbackQueryHandler(handle_boolean_selection, pattern="^bool:"))
    application.add_handler(CallbackQueryHandler(handle_proficiency_selection, pattern="^prof:"))
