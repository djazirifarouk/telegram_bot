import logging
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.keyboards.menus import get_archive_menu, get_cancel_button
from utils.state_manager import state_manager

logger = logging.getLogger(__name__)


async def show_archive_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show archive management menu."""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "🗄️ *Archive Management*\n\nSelect an action:",
        reply_markup=get_archive_menu(),
        parse_mode='Markdown'
    )


async def start_archive_applicant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start archive applicant flow."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state_manager.set_state(user_id, {"action": "archive"})
    
    await query.message.edit_text(
        "📦 *Archive Applicant*\n\nSend the applicant's alias email or phone number:",
        reply_markup=get_cancel_button("archive"),
        parse_mode='Markdown'
    )


async def start_restore_applicant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start restore applicant flow."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state_manager.set_state(user_id, {"action": "restore"})
    
    await query.message.edit_text(
        "♻️ *Restore Applicant*\n\nSend the applicant's alias email or phone number:",
        reply_markup=get_cancel_button("archive"),
        parse_mode='Markdown'
    )


def register_archive_handlers(application):
    """Register archive-related handlers."""
    application.add_handler(CallbackQueryHandler(show_archive_menu, pattern="^archive$"))
    application.add_handler(CallbackQueryHandler(start_archive_applicant, pattern="^arch_archive$"))
    application.add_handler(CallbackQueryHandler(start_restore_applicant, pattern="^arch_restore$"))
