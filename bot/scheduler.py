import asyncio
import logging
from datetime import date, timedelta
from telegram import Bot
from database.supabase_client import supabase
from config.settings import TELEGRAM_TOKEN, ADMIN_CHAT_ID

logger = logging.getLogger(__name__)


async def send_subscription_alerts():
    """Send daily alerts for expired and expiring subscriptions."""
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        today = date.today()
        soon = (today + timedelta(days=7)).isoformat()
        today_str = today.isoformat()
        
        # Get expired subscriptions
        expired_result = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("alias_email, first_name, last_name, whatsapp, subscription_expiration")
            .lt("subscription_expiration", today_str)
            .execute()
        )
        expired = expired_result.data or []
        
        # Get expiring soon subscriptions
        expiring_result = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("alias_email, first_name, last_name, whatsapp, subscription_expiration")
            .gte("subscription_expiration", today_str)
            .lte("subscription_expiration", soon)
            .execute()
        )
        expiring = expiring_result.data or []
        
        # Build message
        message_parts = ["📅 *DAILY SUBSCRIPTION REPORT*\n"]
        message_parts.append(f"Date: {today.strftime('%Y-%m-%d')}\n")
        
        # Expired section
        if expired:
            message_parts.append(f"\n❌ *EXPIRED ({len(expired)}):*\n")
            for u in expired:
                message_parts.append(
                    f"• {u['first_name']} {u['last_name']}\n"
                    f"  📧 {u['alias_email']}\n"
                    f"  📱 {u.get('whatsapp', 'N/A')}\n"
                    f"  ⏰ Expired: {u['subscription_expiration']}\n"
                )
        else:
            message_parts.append("\n✅ No expired subscriptions\n")
        
        # Expiring soon section
        if expiring:
            message_parts.append(f"\n⏳ *EXPIRING SOON (7 days) ({len(expiring)}):*\n")
            for u in expiring:
                days_left = (date.fromisoformat(u['subscription_expiration']) - today).days
                message_parts.append(
                    f"• {u['first_name']} {u['last_name']}\n"
                    f"  📧 {u['alias_email']}\n"
                    f"  📱 {u.get('whatsapp', 'N/A')}\n"
                    f"  ⏰ Expires: {u['subscription_expiration']} ({days_left} days)\n"
                )
        else:
            message_parts.append("\n✅ No subscriptions expiring soon\n")
        
        message = "".join(message_parts)
        
        # Send to admin chat
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        
        logger.info(f"Subscription alert sent: {len(expired)} expired, {len(expiring)} expiring soon")
        
    except Exception as e:
        logger.error(f"Error sending subscription alerts: {e}", exc_info=True)


async def schedule_daily_alerts():
    """Schedule daily alerts at 8 AM."""
    from datetime import datetime
    import time
    
    while True:
        try:
            now = datetime.now()
            # Calculate next 8 AM
            target = now.replace(hour=7, minute=0, second=0, microsecond=0)
            if now >= target:
                # If it's already past 8 AM, schedule for tomorrow
                target = target + timedelta(days=1)
            
            # Calculate seconds until target time
            wait_seconds = (target - now).total_seconds()
            
            logger.info(f"Next subscription alert scheduled for: {target}")
            await asyncio.sleep(wait_seconds)
            
            # Send the alert
            await send_subscription_alerts()
            
            # Wait 60 seconds to avoid running twice at 8 AM
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in scheduler: {e}", exc_info=True)
            await asyncio.sleep(3600)  # Wait 1 hour before retrying
