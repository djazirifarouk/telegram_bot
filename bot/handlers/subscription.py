import logging
import asyncio
from datetime import date, timedelta
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from bot.keyboards.menus import get_subscription_menu, get_cancel_button, get_back_button
from utils.state_manager import state_manager
from database.supabase_client import supabase

logger = logging.getLogger(__name__)


async def show_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription management menu."""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "📅 *Subscription Management*\n\nSelect an action:",
        reply_markup=get_subscription_menu(),
        parse_mode='Markdown'
    )


async def start_set_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start set subscription date flow."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state_manager.set_state(user_id, {"action": "set_sub", "step": "email"})
    
    await query.message.edit_text(
        "📅 *Set Subscription Date*\n\nSend the applicant's alias email or phone number:",
        reply_markup=get_cancel_button("subscription"),
        parse_mode='Markdown'
    )


async def start_extend_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start extend subscription flow."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state_manager.set_state(user_id, {"action": "extend_sub", "step": "email"})
    
    await query.message.edit_text(
        "➕ *Extend Subscription*\n\nSend the applicant's alias email or phone number:",
        reply_markup=get_cancel_button("subscription"),
        parse_mode='Markdown'
    )


async def show_expired_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show expired subscriptions."""
    query = update.callback_query
    await query.answer()
    
    try:
        today_str = date.today().isoformat()
        
        response = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("alias_email, whatsapp, subscription_expiration, first_name, last_name")
            .lt("subscription_expiration", today_str)
            .execute()
        )
        
        expired = response.data or []
        
        if expired:
            message = "❌ *Expired Subscriptions:*\n\n" + "\n".join([
                f"• {u['first_name']} {u['last_name']}\n"
                f"  📧 `{u['alias_email']}`\n"
                f"  📱 {u.get('whatsapp', 'N/A')}\n"
                f"  📅 Expired: {u['subscription_expiration']}\n"
                for u in expired
            ])
        else:
            message = "✅ *No expired subscriptions found!*"
        
        await query.message.edit_text(
            message,
            reply_markup=get_back_button("subscription"),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error getting expired subscriptions: {e}")
        await query.message.edit_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_back_button("subscription")
        )


async def show_expiring_soon_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscriptions expiring in the next 7 days."""
    query = update.callback_query
    await query.answer()
    
    try:
        today = date.today()
        soon = (today + timedelta(days=7)).isoformat()
        today_str = today.isoformat()
        
        response = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("alias_email, whatsapp, subscription_expiration, first_name, last_name")
            .gte("subscription_expiration", today_str)
            .lte("subscription_expiration", soon)
            .execute()
        )
        
        expiring = response.data or []
        
        if expiring:
            message = "⏳ *Subscriptions expiring in 7 days:*\n\n" + "\n".join([
                f"• {u['first_name']} {u['last_name']}\n"
                f"  📧 `{u['alias_email']}`\n"
                f"  📱 {u.get('whatsapp', 'N/A')}\n"
                f"  📅 Expires: {u['subscription_expiration']}\n"
                for u in expiring
            ])
        else:
            message = "✅ *No subscriptions expiring in the next 7 days!*"
        
        await query.message.edit_text(
            message,
            reply_markup=get_back_button("subscription"),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error getting expiring subscriptions: {e}")
        await query.message.edit_text(
            f"❌ Error: {str(e)}",
            reply_markup=get_back_button("subscription")
        )


def register_subscription_handlers(application):
    """Register subscription-related handlers."""
    application.add_handler(CallbackQueryHandler(show_subscription_menu, pattern="^subscription$"))
    application.add_handler(CallbackQueryHandler(start_set_subscription, pattern="^sub_set$"))
    application.add_handler(CallbackQueryHandler(start_extend_subscription, pattern="^sub_extend$"))
    application.add_handler(CallbackQueryHandler(show_expired_subscriptions, pattern="^sub_expired$"))
    application.add_handler(CallbackQueryHandler(show_expiring_soon_subscriptions, pattern="^sub_soon$"))
    