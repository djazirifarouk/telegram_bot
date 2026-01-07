import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from telegram.request import HTTPXRequest
from config.settings import TELEGRAM_TOKEN
from bot.handlers import register_all_handlers
from bot.handlers.text_handler import handle_text_input, handle_cancel_command
import asyncio
from bot.scheduler import schedule_daily_alerts

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Start scheduler after application initialization."""
    asyncio.create_task(schedule_daily_alerts())
    logger.info("📅 Daily subscription alerts scheduler started (9 AM)")


def main():
    """Start the bot."""
    logger.info("=" * 50)
    logger.info("🤖 STARTING APPLICANT MANAGEMENT BOT")
    logger.info("=" * 50)
    
    # Create custom request with longer timeouts
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=60.0,      # Increased from default 5s
        write_timeout=60.0,     # Increased from default 5s
        connect_timeout=60.0,   # Increased from default 5s
        pool_timeout=60.0       # Increased from default 1s
    )
    
    # Create application with custom request
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .request(request)
        .build()
    )
    
    # Register all handlers
    register_all_handlers(application)
    
    # Add cancel command
    application.add_handler(CommandHandler("cancel", handle_cancel_command))
    
    # Register text handler LAST
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input),
        group=1
    )
    
    # Set up post_init to start scheduler
    application.post_init = post_init
    
    logger.info("✅ Bot started successfully!")
    logger.info("📱 Send /start to begin")
    
    # Run the bot
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()