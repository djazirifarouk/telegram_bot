# =============================================================================
# FILE: bot/handlers/text_handler.py - COMPLETE FINAL VERSION
# =============================================================================
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.menus import get_home_button, get_editable_fields_keyboard
from bot.validators.input_validators import (
    validate_subscription_date,
    validate_date_format,
    is_field_optional,
    get_field_prompt
)
from bot.formatters.display import format_nested_array
from database.queries import (
    update_applicant,
    archive_applicant,
    restore_applicant,
    get_applicant,
    download_file_from_storage
)
from utils.helpers import resolve_lookup
from utils.state_manager import state_manager
from config.settings import EDITABLE_FIELDS, NESTED_FIELD_STRUCTURES

logger = logging.getLogger(__name__)


# =============================================================================
# MAIN TEXT INPUT ROUTER
# =============================================================================

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text input based on user state."""
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    
    state = state_manager.get_state(user_id)
    if not state:
        return
    
    action = state.get("action")
    
    # Route to appropriate handler based on action
    if action == "find":
        await handle_find_action(update, text)
    elif action == "mark_done":
        await handle_mark_done_action(update, text)
    elif action == "mark_pending":
        await handle_mark_pending_action(update, text)
    elif action == "set_sub":
        await handle_set_subscription_action(update, text, state)
    elif action == "extend_sub":
        await handle_extend_subscription_action(update, text, state)
    elif action == "edit_field":
        await handle_edit_field_action(update, text, state)
    elif action == "archive":
        await handle_archive_action(update, text)
    elif action == "restore":
        await handle_restore_action(update, text)


# =============================================================================
# FIND APPLICANT
# =============================================================================

async def handle_find_action(update: Update, text: str):
    """Handle finding an applicant."""
    user_id = update.message.from_user.id
    
    try:
        field, value = resolve_lookup(text)
        
        # Search in both tables
        applicant = await get_applicant(field, value, "applications")
        if not applicant:
            applicant = await get_applicant(field, value, "applications_archive")
        
        if not applicant:
            await update.message.reply_text(
                f"❌ No applicant found with {field}: `{text}`",
                reply_markup=get_home_button(),
                parse_mode='Markdown'
            )
            state_manager.clear_state(user_id)
            return
        
        # Send applicant details
        await send_applicant_details(update, applicant)
        
    except Exception as e:
        logger.error(f"Error finding applicant: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_home_button()
        )
    
    state_manager.clear_state(user_id)


async def send_applicant_details(update: Update, a: dict):
    """Send formatted applicant details."""
    # Header
    await update.message.reply_text(
        f"🚨 *APPLICANT DETAILS*\n\n"
        f"👤 {a.get('first_name', '-')} {a.get('last_name', '-')}\n"
        f"✒️ Plan: {a.get('application_plan', '-')}\n"
        f"📧 Alias: `{a.get('alias_email', '-')}`\n"
        f"📧 Personal email: `{a.get('email', '-')}`",
        parse_mode='Markdown'
    )
    
    # Search Preferences
    country_pref = a.get("country_preference")
    if isinstance(country_pref, list):
        country_text = ", ".join(country_pref) if country_pref else "-"
    else:
        country_text = country_pref or "-"
    
    await update.message.reply_text(
        f"🔎 *Search Preferences*\n\n"
        f"Applying for: `{a.get('apply_role', '-')}`\n"
        f"Search AI Accuracy: `{a.get('search_accuracy', '-')}`\n"
        f"Employment Type: `{a.get('employment_type', '-')}`\n"
        f"Country Preference: `{country_text}`",
        parse_mode="Markdown"
    )
    
    # CV
    cv_file = await download_file_from_storage(a.get("cv_url"), "cv")
    if cv_file:
        await update.message.reply_document(document=cv_file, caption="📄 CV")
    
    # Contact Information
    await update.message.reply_text(
        f"📞 *Contact Information*\n\n"
        f"Name: {a.get('first_name','-')} {a.get('last_name','-')}\n"
        f"Email: {a.get('email','-')}\n"
        f"WhatsApp: {a.get('whatsapp','-')}\n"
        f"LinkedIn: {a.get('linkedin','-')}\n"
        f"X/Twitter: {a.get('twitter','-')}\n"
        f"GitHub: {a.get('github','-')}\n"
        f"Portfolio: {a.get('website','-')}",
        parse_mode='Markdown'
    )
    
    # Address Information
    await update.message.reply_text(
        f"🏠 *Address Information*\n\n"
        f"Street: {a.get('street','-')}\n"
        f"Building No: {a.get('building','-')}\n"
        f"Apartment No: {a.get('apartment','-')}\n"
        f"City: {a.get('city','-')}\n"
        f"Country: {a.get('country','-')}\n"
        f"Zip Code: {a.get('zip','-')}",
        parse_mode='Markdown'
    )
    
    # Legalisation
    await update.message.reply_text(
        f"📝 *Legalisation*\n\n"
        f"Authorized Countries: {a.get('autorized_countries','-')}\n"
        f"Visa: {a.get('visa','-')}\n"
        f"Willing to relocation: {a.get('relocate','-')}\n"
        f"Total years of Experience: {a.get('experience','-')} years",
        parse_mode='Markdown'
    )
    
    # Roles
    roles = a.get("roles")
    if not roles:
        roles_text = "-"
    else:
        lines = []
        for r in roles:
            lines.append(
                f"• *{r.get('title','-')}* at {r.get('company','-')}\n"
                f"  📍 {r.get('location','-')}\n"
                f"  🗓️ {r.get('start','-')} → "
                f"{'Present' if r.get('current') else r.get('end','-')}\n"
                f"  📝 {r.get('description','-')}"
            )
        roles_text = "\n\n".join(lines)
    
    await update.message.reply_text(
        f"🎯 *Roles*\n\n{roles_text}",
        parse_mode="Markdown"
    )
    
    # Education
    education = a.get("education")
    if not education:
        education_text = "-"
    else:
        lines = []
        for e in education:
            lines.append(
                f"• *{e.get('degree','-')}* — {e.get('field','-')}\n"
                f"  🏫 {e.get('school','-')}\n"
                f"  🗓️ {e.get('start','-')} → {e.get('end','-')}"
            )
        education_text = "\n\n".join(lines)
    
    await update.message.reply_text(
        f"🎓 *Education*\n\n{education_text}",
        parse_mode="Markdown"
    )
    
    # Certificates
    certificates = a.get("certificates")
    if not certificates:
        certificates_text = "-"
    else:
        lines = []
        for c in certificates:
            lines.append(
                f"• *{c.get('name','-')}*\n"
                f"  🆔 {c.get('number','-')}\n"
                f"  🗓️ {c.get('start','-')} → {c.get('end','-')}"
            )
        certificates_text = "\n\n".join(lines)
    
    await update.message.reply_text(
        f"📜 *Courses & Certificates*\n\n{certificates_text}",
        parse_mode="Markdown"
    )
    
    # Languages
    languages = a.get("languages")
    if not languages:
        languages_text = "-"
    else:
        lines = []
        for l in languages:
            lines.append(
                f"• *{l.get('language','-')}* — {l.get('proficiency','-')}"
            )
        languages_text = "\n".join(lines)
    
    await update.message.reply_text(
        f"🌍 *Languages*\n\n{languages_text}",
        parse_mode="Markdown"
    )
    
    # Skills
    skills = a.get("skills")
    if isinstance(skills, list):
        skills_text = ", ".join(skills) if skills else "-"
    else:
        skills_text = skills or "-"
    
    await update.message.reply_text(
        f"🎯 *Skills*\n\n{skills_text}",
        parse_mode="Markdown"
    )
    
    # Compensation
    await update.message.reply_text(
        f"💰 *Compensation Details*\n\n"
        f"Expected Salary: {a.get('expected_salary_currency','-')} {a.get('expected_salary','-')}\n"
        f"Current Salary: {a.get('expected_salary_currency','-')} {a.get('current_salary','-')}\n"
        f"Payment Status: {a.get('payment','-')}",
        parse_mode='Markdown'
    )
    
    # Achievements
    await update.message.reply_text(
        f"🏆 *Achievements*\n\n{a.get('achievements','-')}",
        parse_mode='Markdown'
    )
    
    # Profile picture
    picture_file = await download_file_from_storage(a.get("picture_url"), "pictures")
    if picture_file:
        await update.message.reply_document(document=picture_file, caption="📸 Profile Picture")
    
    await update.message.reply_text(
        "✅ All details sent!",
        reply_markup=get_home_button()
    )


# =============================================================================
# PAYMENT MANAGEMENT
# =============================================================================

async def handle_mark_done_action(update: Update, text: str):
    """Handle marking payment as done."""
    user_id = update.message.from_user.id
    
    try:
        field, value = resolve_lookup(text)
        success = await update_applicant(field, value, {"payment": "done"})
        
        if success:
            await update.message.reply_text(
                f"✅ Payment marked as *done* for:\n`{text}`",
                reply_markup=get_home_button(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Error marking payment as done",
                reply_markup=get_home_button()
            )
    except Exception as e:
        logger.error(f"Error in mark_done: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_home_button()
        )
    
    state_manager.clear_state(user_id)


async def handle_mark_pending_action(update: Update, text: str):
    """Handle marking payment as pending."""
    user_id = update.message.from_user.id
    
    try:
        field, value = resolve_lookup(text)
        success = await update_applicant(field, value, {"payment": "pending"})
        
        if success:
            await update.message.reply_text(
                f"⏳ Payment marked as *pending* for:\n`{text}`",
                reply_markup=get_home_button(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Error marking payment as pending",
                reply_markup=get_home_button()
            )
    except Exception as e:
        logger.error(f"Error in mark_pending: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_home_button()
        )
    
    state_manager.clear_state(user_id)


# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

async def handle_set_subscription_action(update: Update, text: str, state: dict):
    """Handle setting subscription date."""
    user_id = update.message.from_user.id
    step = state.get("step")
    
    if step == "email":
        state_manager.update_state(user_id, {"step": "date", "email": text})
        await update.message.reply_text(
            f"📅 Email: `{text}`\n\nNow send the subscription expiration date (YYYY-MM-DD):",
            parse_mode='Markdown'
        )
    
    elif step == "date":
        is_valid, error_msg = validate_subscription_date(text)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {error_msg}\n\nPlease send a valid date in format: *YYYY-MM-DD*",
                parse_mode='Markdown'
            )
            return
        
        email = state.get("email")
        field, value = resolve_lookup(email)
        
        success = await update_applicant(field, value, {"subscription_expiration": text})
        
        if success:
            await update.message.reply_text(
                f"✅ Subscription set for:\n`{value}`\nUntil: *{text}*",
                reply_markup=get_home_button(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Error setting subscription",
                reply_markup=get_home_button()
            )
        
        state_manager.clear_state(user_id)


async def handle_extend_subscription_action(update: Update, text: str, state: dict):
    """Handle extending subscription."""
    user_id = update.message.from_user.id
    step = state.get("step")
    
    if step == "email":
        state_manager.update_state(user_id, {"step": "days", "email": text})
        await update.message.reply_text(
            f"➕ Email: `{text}`\n\nNow send the number of days to extend:",
            parse_mode='Markdown'
        )
    
    elif step == "days":
        email = state.get("email")
        
        try:
            days = int(text)
            field, value = resolve_lookup(email)
            
            applicant = await get_applicant(field, value)
            
            if not applicant:
                await update.message.reply_text(
                    f"❌ No applicant found with: `{email}`",
                    reply_markup=get_home_button(),
                    parse_mode='Markdown'
                )
                state_manager.clear_state(user_id)
                return
            
            current_exp_str = applicant.get("subscription_expiration")
            if not current_exp_str:
                await update.message.reply_text(
                    f"❌ No subscription date set for this applicant.\nPlease set a subscription date first.",
                    reply_markup=get_home_button(),
                    parse_mode='Markdown'
                )
                state_manager.clear_state(user_id)
                return
            
            current_exp = datetime.strptime(current_exp_str, "%Y-%m-%d")
            new_exp = (current_exp + timedelta(days=days)).date()
            
            success = await update_applicant(field, value, {"subscription_expiration": new_exp.isoformat()})
            
            if success:
                await update.message.reply_text(
                    f"✅ Subscription extended for:\n`{email}`\n"
                    f"New expiration: *{new_exp}*\n(+{days} days)",
                    reply_markup=get_home_button(),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Error extending subscription",
                    reply_markup=get_home_button()
                )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid number. Please send a valid number of days.",
                parse_mode='Markdown'
            )
            return
        except Exception as e:
            logger.error(f"Error extending subscription: {e}")
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                reply_markup=get_home_button()
            )
        
        state_manager.clear_state(user_id)


# =============================================================================
# EDIT FIELD
# =============================================================================

async def handle_edit_field_action(update: Update, text: str, state: dict):
    """Handle editing field value."""
    user_id = update.message.from_user.id
    step = state.get("step")
    
    if step == "identify":
        field, value = resolve_lookup(text)
        applicant = await get_applicant(field, value)
        
        if not applicant:
            await update.message.reply_text(
                "❌ Applicant not found.",
                reply_markup=get_home_button()
            )
            state_manager.clear_state(user_id)
            return
        
        state_manager.update_state(user_id, {
            "step": "choose_field",
            "lookup_field": field,
            "lookup_value": value,
            "applicant": applicant
        })
        
        await update.message.reply_text(
            "🧩 *Select field to edit:*",
            reply_markup=get_editable_fields_keyboard(),
            parse_mode="Markdown"
        )
    
    elif step == "edit_value":
        col = state["column"]
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]
        
        success = await update_applicant(lookup_field, lookup_value, {col: text})
        
        if success:
            await update.message.reply_text(
                f"✅ *Updated {EDITABLE_FIELDS[col]} successfully!*",
                reply_markup=get_home_button(),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ Error updating field",
                reply_markup=get_home_button()
            )
        
        state_manager.clear_state(user_id)
    
    elif step == "nested_input":
        await process_nested_field_input(update, text, state)


# =============================================================================
# NESTED FIELD INPUT PROCESSING
# =============================================================================

async def process_nested_field_input(update: Update, text: str, state: dict):
    """Process input for nested field creation/editing with validation."""
    user_id = update.effective_user.id
    
    field_type = state["nested_type"]
    structure = NESTED_FIELD_STRUCTURES[field_type]
    fields = structure["fields"]
    labels = structure["labels"]
    field_types = structure.get("types", {})
    current_field_idx = state["nested_field_index"]
    current_field = fields[current_field_idx]
    
    # Handle skip/empty for optional fields
    if text.lower() in ['skip', 'empty'] and is_field_optional(field_type, current_field):
        text = ""
    
    # Validate date fields
    if current_field in field_types and field_types[current_field] == "date":
        is_valid, error_msg = validate_date_format(text)
        
        if not is_valid:
            retry_prompt = f"❌ {error_msg}\n\n{get_field_prompt(field_type, current_field, labels)}"
            
            if update.callback_query:
                await update.callback_query.message.reply_text(retry_prompt, parse_mode="Markdown")
            else:
                await update.message.reply_text(retry_prompt, parse_mode="Markdown")
            return
    
    # Store the input
    state["nested_data"][current_field] = text
    
    # Move to next field
    next_field_idx = current_field_idx + 1
    
    if next_field_idx < len(fields):
        state_manager.update_state(user_id, {"nested_field_index": next_field_idx})
        next_field = fields[next_field_idx]
        next_label = labels[next_field]
        
        # Get current value if editing
        current_val = ""
        if state.get("nested_action") == "edit" and "nested_entry_index" in state:
            applicant = state.get("applicant", {})
            current_data = applicant.get(field_type, [])
            entry_idx = state.get("nested_entry_index")
            if entry_idx < len(current_data):
                current_val = current_data[entry_idx].get(next_field, "")
        
        # Check if next field is boolean or select
        if next_field in field_types:
            if field_types[next_field] == "boolean":
                from bot.keyboards.menus import get_boolean_keyboard
                
                prompt = f"Select *{next_label}*:"
                if current_val:
                    prompt = f"Current: *{current_val}*\n\n{prompt}"
                
                keyboard = get_boolean_keyboard(next_field)
                
                if update.callback_query:
                    await update.callback_query.message.edit_text(
                        prompt,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        prompt,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                return
                
            elif field_types[next_field] == "select" and next_field == "proficiency":
                from bot.keyboards.menus import get_proficiency_keyboard
                
                prompt = f"Select *{next_label}*:"
                if current_val:
                    prompt = f"Current: *{current_val}*\n\n{prompt}"
                
                keyboard = get_proficiency_keyboard()
                
                if update.callback_query:
                    await update.callback_query.message.edit_text(
                        prompt,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        prompt,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                return
        
        # Regular text field
        prompt = get_field_prompt(field_type, next_field, labels, is_editing=bool(current_val), current_value=current_val)
        
        if update.callback_query:
            await update.callback_query.message.reply_text(prompt, parse_mode="Markdown")
        else:
            await update.message.reply_text(prompt, parse_mode="Markdown")
    else:
        # All fields collected, save to database
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]
        nested_action = state["nested_action"]
        
        applicant = await get_applicant(lookup_field, lookup_value)
        if not applicant:
            message_text = "❌ Applicant not found."
            if update.callback_query:
                await update.callback_query.message.reply_text(message_text)
            else:
                await update.message.reply_text(message_text)
            state_manager.clear_state(user_id)
            return
        
        current_data = applicant.get(field_type, [])
        if not isinstance(current_data, list):
            current_data = []
        
        if nested_action == "add":
            current_data.append(state["nested_data"])
        elif nested_action == "edit":
            entry_index = state["nested_entry_index"]
            if entry_index < len(current_data):
                current_data[entry_index] = state["nested_data"]
        
        success = await update_applicant(lookup_field, lookup_value, {field_type: current_data})
        
        if success:
            success_msg = f"✅ *{EDITABLE_FIELDS[field_type]} {'added' if nested_action == 'add' else 'updated'} successfully!*"
            
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    success_msg,
                    reply_markup=get_home_button(),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    success_msg,
                    reply_markup=get_home_button(),
                    parse_mode="Markdown"
                )
        else:
            error_msg = "❌ Error updating data"
            if update.callback_query:
                await update.callback_query.message.reply_text(error_msg, reply_markup=get_home_button())
            else:
                await update.message.reply_text(error_msg, reply_markup=get_home_button())
        
        state_manager.clear_state(user_id)


# =============================================================================
# ARCHIVE MANAGEMENT
# =============================================================================

async def handle_archive_action(update: Update, text: str):
    """Handle archiving applicant."""
    user_id = update.message.from_user.id
    
    try:
        field, value = resolve_lookup(text)
        success = await archive_applicant(field, value)
        
        if success:
            await update.message.reply_text(
                f"✅ Applicant archived:\n`{text}`",
                reply_markup=get_home_button(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ No applicant found with: `{text}`",
                reply_markup=get_home_button(),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error archiving: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_home_button()
        )
    
    state_manager.clear_state(user_id)


async def handle_restore_action(update: Update, text: str):
    """Handle restoring applicant."""
    user_id = update.message.from_user.id
    
    try:
        field, value = resolve_lookup(text)
        success = await restore_applicant(field, value)
        
        if success:
            await update.message.reply_text(
                f"✅ Applicant restored:\n`{text}`",
                reply_markup=get_home_button(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ No archived applicant found with: `{text}`",
                reply_markup=get_home_button(),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error restoring: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_home_button()
        )
    
    state_manager.clear_state(user_id)