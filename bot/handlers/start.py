import logging
from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from bot.keyboards.menus import get_main_menu

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and display main menu."""
    await show_main_menu(update)


async def show_main_menu(update: Update):
    """Display the main menu."""
    message_text = "🤖 *Applicant Management Bot*\n\nSelect an option:"
    reply_markup = get_main_menu()
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def handle_back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button to return to main menu."""
    query = update.callback_query
    await query.answer()
    await show_main_menu(update)


def register_start_handlers(application):
    """Register start-related handlers."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_back_button, pattern="^back$"))
