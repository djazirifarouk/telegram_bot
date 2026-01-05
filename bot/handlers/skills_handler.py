import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.menus import (
    get_skills_menu_keyboard,
    get_home_button,
    get_back_button,
    get_continue_or_home_keyboard
)
from database.queries import update_applicant, get_applicant
from utils.state_manager import state_manager
from config.settings import EDITABLE_FIELDS

logger = logging.getLogger(__name__)


async def handle_skills_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skills menu selection."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split("skills:")[1]
    user_id = query.from_user.id
    state = state_manager.get_state(user_id)
    
    if not state:
        return
    
    applicant = state.get("applicant", {})
    current_skills = applicant.get("skills", [])
    
    if action == "add":
        state_manager.update_state(user_id, {"step": "skills_add"})
        await query.message.edit_text(
            f"➕ *Add Skills*\n\n"
            f"Enter skills separated by commas.\n"
            f"Example: Python, JavaScript, Docker\n\n"
            f"Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    elif action == "remove":
        if not current_skills:
            await query.message.edit_text(
                "❌ No skills to remove.",
                reply_markup=get_back_button("back_to_fields")
            )
            return
        
        state_manager.update_state(user_id, {"step": "skills_remove"})
        skills_text = ", ".join(current_skills)
        await query.message.edit_text(
            f"🗑️ *Remove Skills*\n\n"
            f"Current skills: {skills_text}\n\n"
            f"Enter skills to remove (separated by commas):\n\n"
            f"Send /cancel to abort.",
            parse_mode="Markdown"
        )
    
    elif action == "view":
        if not current_skills:
            skills_display = "None"
        else:
            skills_display = "\n".join([f"• {skill}" for skill in current_skills])
        
        await query.message.edit_text(
            f"📋 *Current Skills*\n\n{skills_display}",
            reply_markup=get_back_button("back_to_fields"),
            parse_mode="Markdown"
        )


async def handle_skills_add(update: Update, text: str, state: dict):
    """Handle adding skills."""
    user_id = update.message.from_user.id
    
    # Parse skills from comma-separated text
    new_skills = [s.strip() for s in text.split(",") if s.strip()]
    
    if not new_skills:
        await update.message.reply_text(
            "❌ No skills entered. Please try again.\n\n"
            "Send /cancel to abort."
        )
        return
    
    lookup_field = state["lookup_field"]
    lookup_value = state["lookup_value"]
    
    # Get current skills
    applicant = await get_applicant(lookup_field, lookup_value)
    current_skills = applicant.get("skills", [])
    if not isinstance(current_skills, list):
        current_skills = []
    
    # Add new skills (avoid duplicates)
    for skill in new_skills:
        if skill not in current_skills:
            current_skills.append(skill)
    
    success = await update_applicant(lookup_field, lookup_value, {"skills": current_skills})
    
    if success:
        added_text = ", ".join(new_skills)
        await update.message.reply_text(
            f"✅ *Skills added!*\n\nAdded: {added_text}\n\n"
            f"Total skills: {len(current_skills)}",
            reply_markup=get_home_button(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Error updating skills",
            reply_markup=get_home_button()
        )
    
    state_manager.clear_state(user_id)


async def handle_skills_remove(update: Update, text: str, state: dict):
    """Handle removing skills."""
    user_id = update.message.from_user.id
    
    # Parse skills to remove
    skills_to_remove = [s.strip() for s in text.split(",") if s.strip()]
    
    if not skills_to_remove:
        await update.message.reply_text(
            "❌ No skills entered. Please try again.\n\n"
            "Send /cancel to abort."
        )
        return
    
    lookup_field = state["lookup_field"]
    lookup_value = state["lookup_value"]
    
    # Get current skills
    applicant = await get_applicant(lookup_field, lookup_value)
    current_skills = applicant.get("skills", [])
    if not isinstance(current_skills, list):
        current_skills = []
    
    # Remove skills
    removed = []
    for skill in skills_to_remove:
        if skill in current_skills:
            current_skills.remove(skill)
            removed.append(skill)
    
    if not removed:
        await update.message.reply_text(
            f"❌ None of the specified skills were found.\n\n"
            f"Current skills: {', '.join(current_skills)}",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)
        return
    
    success = await update_applicant(lookup_field, lookup_value, {"skills": current_skills})
    
    if success:
        removed_text = ", ".join(removed)
        await update.message.reply_text(
            f"✅ *Skills removed!*\n\nRemoved: {removed_text}\n\n"
            f"Remaining skills: {len(current_skills)}",
            reply_markup=get_home_button(),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Error updating skills",
            reply_markup=get_home_button()
        )
    
    state_manager.clear_state(user_id)


def register_skills_handlers(application):
    """Register skills-related handlers."""
    from bot.handlers.edit import handle_country_selection  # Import here
    
    application.add_handler(CallbackQueryHandler(handle_skills_menu, pattern="^skills:"))
    application.add_handler(CallbackQueryHandler(handle_country_selection, pattern="^country:"))
