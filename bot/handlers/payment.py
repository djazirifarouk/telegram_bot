import logging
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.keyboards.menus import get_payment_menu, get_cancel_button, get_home_button
from database.queries import update_applicant
from utils.helpers import resolve_lookup
from utils.state_manager import state_manager

logger = logging.getLogger(__name__)


async def show_payment_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment management menu."""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "💰 *Payment Management*\n\nSelect an action:",
        reply_markup=get_payment_menu(),
        parse_mode='Markdown'
    )


async def start_mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start mark payment as done flow."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state_manager.set_state(user_id, {"action": "mark_done"})
    
    await query.message.edit_text(
        "✅ *Mark Payment as Done*\n\nSend the applicant's alias email or phone number:",
        reply_markup=get_cancel_button("payment"),
        parse_mode='Markdown'
    )


async def start_mark_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start mark payment as pending flow."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state_manager.set_state(user_id, {"action": "mark_pending"})
    
    await query.message.edit_text(
        "⏳ *Mark Payment as Pending*\n\nSend the applicant's alias email or phone number:",
        reply_markup=get_cancel_button("payment"),
        parse_mode='Markdown'
    )


def register_payment_handlers(application):
    """Register payment-related handlers."""
    application.add_handler(CallbackQueryHandler(show_payment_menu, pattern="^payment$"))
    application.add_handler(CallbackQueryHandler(start_mark_done, pattern="^pay_done$"))
    application.add_handler(CallbackQueryHandler(start_mark_pending, pattern="^pay_pending$"))
