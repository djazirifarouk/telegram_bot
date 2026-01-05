import logging
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.keyboards.menus import get_back_button
from database.queries import get_statistics

logger = logging.getLogger(__name__)


async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show application statistics."""
    query = update.callback_query
    await query.answer()
    
    try:
        stats = await get_statistics()
        
        # Format plan statistics
        plan_stats = "\n".join([
            f"• {p['application_plan']}: {p['count']}" 
            for p in stats['plans'] 
            if p.get("application_plan")
        ])
        
        message = (
            f"📊 *Statistics*\n\n"
            f"⏳ Pending: {stats['pending']}\n"
            f"✅ Done: {stats['done']}\n"
            f"📦 Archived: {stats['archived']}\n\n"
            f"✒️ *Applicants per Plan*\n\n"
            f"{plan_stats or 'No plans found'}\n"
            f"➖➖➖➖➖➖➖\n"
            f"📈 Total Active: {stats['total']}"
        )
        
        await query.message.edit_text(
            message,
            reply_markup=get_back_button("back"),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error showing statistics: {e}")
        await query.message.edit_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_back_button("back")
        )


def register_stats_handlers(application):
    """Register statistics-related handlers."""
    application.add_handler(CallbackQueryHandler(show_statistics, pattern="^stats$"))
