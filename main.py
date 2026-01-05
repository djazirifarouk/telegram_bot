import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from config.settings import TELEGRAM_TOKEN
from bot.handlers import register_all_handlers
from bot.handlers.text_handler import handle_text_input

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    logger.info("=" * 50)
    logger.info("🤖 STARTING APPLICANT MANAGEMENT BOT")
    logger.info("=" * 50)
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register all handlers
    register_all_handlers(application)
    
    # Register text handler (should be last)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
    )
    
    # Start bot
    logger.info("✅ Bot started successfully!")
    logger.info("📱 Send /start to begin")
    
    # Run the bot
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()