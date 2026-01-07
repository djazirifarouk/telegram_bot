import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.menus import (
    get_home_button,
    get_editable_fields_keyboard,
    get_country_suggestions,
    get_continue_or_home_keyboard
)
from bot.validators.input_validators import (
    validate_subscription_date,
    validate_date_format,
    is_field_optional,
    get_field_prompt
)
from bot.formatters.display import format_nested_array
from bot.handlers.skills_handler import handle_skills_add, handle_skills_remove
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
    step = state.get("step")
    
    # Check for cancel
    if text.lower() == '/cancel':
        await handle_cancel_command(update, context)
        return
    
    # Route based on action and step
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
        # Handle different edit steps
        if step == "identify":
            await handle_edit_identify(update, text)
        elif step == "text_input":
            await handle_text_field_update(update, text, state)
        elif step == "number_input":
            await handle_number_input(update, text, state)
        elif step == "country_select":  # ADD THIS
            await handle_country_typing(update, text, state)
        elif step == "nested_input":
            await process_nested_field_input(update, text, state)
        elif step == "skills_add":
            await handle_skills_add(update, text, state)
        elif step == "skills_remove":
            await handle_skills_remove(update, text, state)
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
    """Send formatted applicant details - COMPLETE WITH ALL FIELDS."""
    from database.queries import download_file_from_storage
    
    # Prepare all messages first (no await)
    messages = []
    # Header
    messages.append((
        f"🚨 *APPLICANT DETAILS*\n\n"
        f"👤 {a.get('first_name', '-')} {a.get('last_name', '-')}\n"
        f"✒️ Plan: {a.get('application_plan', '-')}\n"
        f"📧 Alias: `{a.get('alias_email', '-')}`\n"
        f"📧 Personal email: `{a.get('email', '-')}`"
    ))
    
    # Search Preferences & Application Info
    country_pref = a.get("country_preference")
    if isinstance(country_pref, list):
        country_text = ", ".join(country_pref) if country_pref else "-"
    else:
        country_text = country_pref or "-"
    
    messages.append((
        f"🔎 *Search Preferences*\n\n"
        f"Applying for: `{a.get('apply_role', '-')}`\n"
        f"Search AI Accuracy: `{a.get('search_accuracy', '-')}`\n"
        f"Employment Type: `{a.get('employment_type', '-')}`\n"
        f"Country Preference: `{country_text}`"
    ))
    
    # CV
    cv_file = await download_file_from_storage(a.get("cv_url"), "cv")
    if cv_file:
        await update.message.reply_document(document=cv_file, caption="📄 CV")
    
    # Profile Picture
    picture_file = await download_file_from_storage(a.get("picture_url"), "pictures")
    if picture_file:
        await update.message.reply_document(document=picture_file, caption="📸 Profile Picture")
    
    # Recommendation Letters
    logger.info(f"=== CHECKING RECOMMENDATION LETTERS ===")
    logger.info(f"recommendation_url field value: {a.get('recommendation_url')}")
    logger.info(f"Type: {type(a.get('recommendation_url'))}")
    rec_letters_urls = a.get("recommendation_url", [])
    logger.info(f"rec_letters_urls after .get(): {rec_letters_urls}")
    
    if rec_letters_urls and isinstance(rec_letters_urls, list) and len(rec_letters_urls) > 0:
        logger.info(f"ENTERING recommendation letters block with {len(rec_letters_urls)} letters")
        await update.message.reply_text(
            f"📝 *Recommendation Letters*\n\nTotal: {len(rec_letters_urls)} letter(s)\n\nDownloading...",
            parse_mode='Markdown'
        )
        
        for i, letter_url in enumerate(rec_letters_urls, 1):
            try:
                logger.info(f"Downloading recommendation letter {i}: {letter_url}")
                
                # Download the file from storage
                letter_file = await download_file_from_storage(letter_url, "letters")
                
                if letter_file:
                    await update.message.reply_document(
                        document=letter_file,
                        caption=f"📝 Recommendation Letter {i}/{len(rec_letters_urls)}"
                    )
                    logger.info(f"Successfully sent recommendation letter {i}")
                else:
                    logger.warning(f"Could not download letter {i}: {letter_url}")
                    await update.message.reply_text(f"⚠️ Letter {i} could not be downloaded")
                    
            except Exception as e:
                logger.error(f"Error with recommendation letter {i}: {e}", exc_info=True)
                await update.message.reply_text(f"❌ Error with letter {i}")

    # Contact Information
    messages.append((
        f"📞 *Contact Information*\n\n"
        f"Name: {a.get('first_name','-')} {a.get('last_name','-')}\n"
        f"Email: {a.get('email','-')}\n"
        f"WhatsApp: {a.get('whatsapp','-')}\n"
        f"LinkedIn: {a.get('linkedin','-')}\n"
        f"X/Twitter: {a.get('twitter','-')}\n"
        f"GitHub: {a.get('github','-')}\n"
        f"Portfolio: {a.get('website','-')}"
    ))
    
    # Address Information
    messages.append((
        f"🏠 *Address Information*\n\n"
        f"Street: {a.get('street','-')}\n"
        f"Building No: {a.get('building','-')}\n"
        f"Apartment No: {a.get('apartment','-')}\n"
        f"City: {a.get('city','-')}\n"
        f"Country: {a.get('country','-')}\n"
        f"Zip Code: {a.get('zip','-')}"
    ))
    
    # Legalisation & Work Authorization
    auth_countries = a.get("authorized_countries", [])
    if isinstance(auth_countries, list):
        auth_text = ", ".join(auth_countries) if auth_countries else "-"
    else:
        auth_text = auth_countries or "-"
    
    messages.append((
        f"📝 *Legalisation & Authorization*\n\n"
        f"Authorized Countries: {auth_text}\n"
        f"Visa: {a.get('visa','-')}\n"
        f"Willing to Relocate: {a.get('relocate','-')}\n"
        f"Total Years of Experience: {a.get('experience','-')} years"
    ))
    
    # Roles/Work Experience
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
    
    messages.append((
        f"🎯 *Work Experience*\n\n{roles_text}"
    ))
    
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
    
    messages.append((
        f"🎓 *Education*\n\n{education_text}"
    ))
    
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
    
    messages.append((
        f"📜 *Courses & Certificates*\n\n{certificates_text}"
    ))
    
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
    
    messages.append((
        f"🌍 *Languages*\n\n{languages_text}"
    ))
    
    # Skills
    skills = a.get("skills")
    if isinstance(skills, list):
        skills_text = ", ".join(skills) if skills else "-"
    else:
        skills_text = skills or "-"
    
    messages.append((
        f"🎯 *Skills*\n\n{skills_text}"
    ))
    
    # Achievements
    achievements = a.get("achievements", "-")
    messages.append((
        f"🏆 *Achievements*\n\n{achievements}"
    ))
    
    # Compensation & Salary
    messages.append((
        f"💰 *Compensation Details*\n\n"
        f"Current Salary: {a.get('current_salary_currency', a.get('expected_salary_currency', '-'))} {a.get('current_salary','-')}\n"
        f"Expected Salary: {a.get('expected_salary_currency','-')} {a.get('expected_salary','-')}\n"
        f"Notice Period: {a.get('notice_period','-')} days\n"
        f"Payment Status: {a.get('payment','-')}"
    ))
    
    # Subscription Info
    sub_exp = a.get('subscription_expiration', '-')
    messages.append((
        f"📅 *Subscription*\n\n"
        f"Expires: {sub_exp}"
    ))

    # Send all text messages quickly
    for msg in messages:
        await update.message.reply_text(msg, parse_mode='Markdown')
        await asyncio.sleep(0.1)  # Small delay to avoid rate limits
    
    from bot.keyboards.menus import get_home_button
    await update.message.reply_text(
        "✅ All details sent!",
        reply_markup=get_home_button()
    )


# =============================================================================
# PAYMENT MANAGEMENT
# =============================================================================

async def handle_mark_done_action(update: Update, text: str):
    """Handle marking payment as done and log to purchase history."""
    user_id = update.message.from_user.id
    
    try:
        field, value = resolve_lookup(text)
        
        # Get applicant info first
        applicant = await get_applicant(field, value)
        if not applicant:
            await update.message.reply_text(
                "❌ Applicant not found.",
                reply_markup=get_home_button()
            )
            state_manager.clear_state(user_id)
            return
        
        # Update payment status
        success = await update_applicant(field, value, {"payment": "done"})
        
        if success:
            # Log purchase to history
            from database.queries import log_purchase
            await log_purchase(
                alias_email=applicant.get('alias_email'),
                whatsapp=applicant.get('whatsapp'),
                plan=applicant.get('application_plan', 'Unknown'),
                notes=f"Payment marked as done by admin"
            )
            
            await update.message.reply_text(
                f"✅ Payment marked as *done* for:\n`{text}`\n\n"
                f"📝 Purchase logged to history",
                reply_markup=get_home_button(),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Error marking payment",
                reply_markup=get_home_button()
            )
    except Exception as e:
        logger.error(f"Error in mark_done: {e}", exc_info=True)
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


async def handle_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command to abort current operation."""
    user_id = update.message.from_user.id
    state = state_manager.get_state(user_id)
    
    if not state:
        await update.message.reply_text(
            "Nothing to cancel. Use /start to begin.",
            reply_markup=get_home_button()
        )
        return
    
    state_manager.clear_state(user_id)
    await update.message.reply_text(
        "✅ Operation cancelled.",
        reply_markup=get_home_button()
    )


async def handle_edit_identify(update: Update, text: str):
    """Handle applicant identification for editing."""
    user_id = update.message.from_user.id
    
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


async def handle_text_field_update(update: Update, text: str, state: dict):
    """Handle simple text field updates."""
    user_id = update.message.from_user.id
    col = state["column"]
    lookup_field = state["lookup_field"]
    lookup_value = state["lookup_value"]
    
    success = await update_applicant(lookup_field, lookup_value, {col: text})
    
    if success:
        await update.message.reply_text(
            f"✅ *{EDITABLE_FIELDS.get(col, col)} updated successfully!*",
            reply_markup=get_continue_or_home_keyboard(),
            parse_mode="Markdown"
        )
        # DON'T clear state
    else:
        await update.message.reply_text(
            "❌ Error updating field",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)


async def handle_number_input(update: Update, text: str, state: dict):
    """Handle number input with validation."""
    user_id = update.message.from_user.id
    col = state["column"]
    min_val = state.get("min", 0)
    max_val = state.get("max", 999999)
    
    try:
        number = int(text)
        
        if number < min_val or number > max_val:
            await update.message.reply_text(
                f"❌ Please enter a number between {min_val} and {max_val}.\n\n"
                f"Send /cancel to abort.",
                parse_mode="Markdown"
            )
            return
        
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]
        
        success = await update_applicant(lookup_field, lookup_value, {col: number})
        
        if success:
            await update.message.reply_text(
                f"✅ *{EDITABLE_FIELDS.get(col, col)} updated to: {number}*",
                reply_markup=get_continue_or_home_keyboard(),
                parse_mode="Markdown"
            )
            # DON'T clear state
        else:
            await update.message.reply_text(
                "❌ Error updating field",
                reply_markup=get_home_button()
            )
            state_manager.clear_state(user_id)
        
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid number. Please enter a valid number.\n\n"
            f"Send /cancel to abort.",
            parse_mode="Markdown"
        )


async def handle_country_typing(update: Update, text: str, state: dict):
    """Handle country typing with autocomplete suggestions."""
    user_id = update.message.from_user.id
    
    # Import here to avoid circular import
    from config.settings import COUNTRIES_LIST
    from bot.keyboards.menus import get_country_suggestions
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Find matching countries
    matches = [c for c in COUNTRIES_LIST if c.lower().startswith(text.lower())]
    
    if not matches:
        await update.message.reply_text(
            f"❌ No countries found starting with '{text}'.\n\n"
            f"Please try again or send /cancel to abort.",
            parse_mode="Markdown"
        )
        return
    
    # Show suggestions (max 10)
    matches = matches[:10]
    keyboard = []
    for country in matches:
        keyboard.append([InlineKeyboardButton(country, callback_data=f"country:{country}")])
    
    # Add done button
    keyboard.append([InlineKeyboardButton("✅ Done Adding", callback_data="country:done")])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back_to_fields")])
    
    selected = state.get("selected_countries", [])
    selected_text = ", ".join(selected) if selected else "None yet"
    
    await update.message.reply_text(
        f"🌍 *Country Selection*\n\n"
        f"Selected: {selected_text}\n\n"
        f"Choose from suggestions:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
