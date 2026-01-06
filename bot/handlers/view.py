import logging
from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters
from bot.keyboards.menus import get_view_menu, get_back_button, get_cancel_button, get_home_button
from bot.formatters.display import format_applicant_list
from database.queries import (
    get_applicants_by_status,
    get_archived_applicants,
    get_applicant,
    download_file_from_storage
)
import asyncio
from utils.helpers import resolve_lookup
from utils.state_manager import state_manager

logger = logging.getLogger(__name__)


async def show_view_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show view applicants submenu."""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "📋 *View Applicants*\n\nSelect a category:",
        reply_markup=get_view_menu(),
        parse_mode='Markdown'
    )


async def view_pending_applicants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending applicants."""
    query = update.callback_query
    await query.answer()
    
    try:
        users = await get_applicants_by_status("pending")
        
        if not users:
            message = "⏳ *Pending Applicants*\n\nNo pending applicants found."
        else:
            formatted_list = format_applicant_list(users, "•")
            message = f"⏳ *Pending Applicants:*\n\n{formatted_list}"
        
        await query.message.edit_text(
            message,
            reply_markup=get_back_button("view"),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error viewing pending applicants: {e}")
        await query.message.edit_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_back_button("view")
        )


async def view_done_applicants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show done applicants."""
    query = update.callback_query
    await query.answer()
    
    try:
        users = await get_applicants_by_status("done")
        
        if not users:
            message = "✅ *Done Applicants*\n\nNo done applicants found."
        else:
            formatted_list = format_applicant_list(users, "•")
            message = f"✅ *Done Applicants:*\n\n{formatted_list}"
        
        await query.message.edit_text(
            message,
            reply_markup=get_back_button("view"),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error viewing done applicants: {e}")
        await query.message.edit_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_back_button("view")
        )


async def view_archived_applicants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show archived applicants."""
    query = update.callback_query
    await query.answer()
    
    try:
        users = await get_archived_applicants()
        
        if not users:
            message = "📦 *Archived Applicants*\n\nNo archived applicants found."
        else:
            formatted_list = format_applicant_list(users, "•")
            message = f"📦 *Archived Applicants:*\n\n{formatted_list}"
        
        await query.message.edit_text(
            message,
            reply_markup=get_back_button("view"),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error viewing archived applicants: {e}")
        await query.message.edit_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_back_button("view")
        )


async def start_find_applicant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start find applicant flow."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state_manager.set_state(user_id, {"action": "find"})
    
    await query.message.edit_text(
        "🔍 *Find Applicant*\n\nSend the applicant's alias email or phone number:",
        reply_markup=get_cancel_button("back"),
        parse_mode='Markdown'
    )


async def process_find_applicant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process find applicant request."""
    user_id = update.message.from_user.id
    state = state_manager.get_state(user_id)
    
    if state.get("action") != "find":
        return
    
    text = update.message.text.strip()
    await find_applicant_details(update, text)
    state_manager.clear_state(user_id)


async def find_applicant_details(update: Update, text: str):
    """Display full applicant details."""
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
            return
        
        # Send applicant details in chunks
        await send_applicant_details(update, applicant)
        
    except Exception as e:
        logger.error(f"Error finding applicant: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_home_button()
        )

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
    rec_letters = a.get("recommendation_url", [])
    if rec_letters and isinstance(rec_letters, list):
        messages.append((
            f"📝 *Recommendation Letters*\n\n"
            f"Total: {len(rec_letters)} letter(s)\n\n"
            f"URLs:\n" + "\n".join([f"• {url}" for url in rec_letters])
        ))
    
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



def register_view_handlers(application):
    """Register view-related handlers."""
    application.add_handler(CallbackQueryHandler(show_view_menu, pattern="^view$"))
    application.add_handler(CallbackQueryHandler(view_pending_applicants, pattern="^view_pending$"))
    application.add_handler(CallbackQueryHandler(view_done_applicants, pattern="^view_done$"))
    application.add_handler(CallbackQueryHandler(view_archived_applicants, pattern="^view_archived$"))
    application.add_handler(CallbackQueryHandler(start_find_applicant, pattern="^find$"))
    # Text handler for find will be registered in main.py with proper priority
