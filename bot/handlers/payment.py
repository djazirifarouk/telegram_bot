import logging
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.keyboards.menus import get_payment_menu, get_cancel_button, get_home_button
from database.queries import update_applicant, get_applicant
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
                amount=applicant.get('expected_salary'),  # Or actual payment amount
                currency=applicant.get('expected_salary_currency', 'USD'),
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


def register_payment_handlers(application):
    """Register payment-related handlers."""
    application.add_handler(CallbackQueryHandler(show_payment_menu, pattern="^payment$"))
    application.add_handler(CallbackQueryHandler(start_mark_done, pattern="^pay_done$"))
    application.add_handler(CallbackQueryHandler(start_mark_pending, pattern="^pay_pending$"))
