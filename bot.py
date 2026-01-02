import os
import io
import asyncio
import urllib.parse
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler, 
    ContextTypes, 
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from supabase import create_client

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Store user state
user_states = {}

# ==================== UTILITY FUNCTIONS ====================

def chunk_text(text: str, chunk_size: int = 4000):
    """Split text into Telegram-safe chunks"""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


async def send_file_from_storage(update: Update, file_url: str, bucket: str, caption: str):
    """Download file from Supabase Storage and send to Telegram"""
    if not file_url:
        return

    try:
        path = urllib.parse.urlparse(file_url).path.split('/')[-1]
        file_bytes = await asyncio.to_thread(lambda: supabase.storage.from_(bucket).download(path))
        file_obj = io.BytesIO(file_bytes)
        file_obj.name = path
        
        if update.callback_query:
            await update.callback_query.message.reply_document(document=file_obj, caption=caption)
        else:
            await update.message.reply_document(document=file_obj, caption=caption)
    except Exception as e:
        logger.error(f"Error sending file: {e}")


# ==================== MAIN MENU ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display main menu"""
    keyboard = [
        [InlineKeyboardButton("📋 View Applicants", callback_data="view")],
        [InlineKeyboardButton("💰 Payment Management", callback_data="payment")],
        [InlineKeyboardButton("📅 Subscription Management", callback_data="subscription")],
        [InlineKeyboardButton("🗄️ Archive Management", callback_data="archive")],
        [InlineKeyboardButton("🔍 Find Applicant", callback_data="find")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = "🤖 *Applicant Management Bot*\n\nSelect an option:"
    
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


# ==================== CALLBACK HANDLER ====================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    logger.info(f"Callback: {data} from user {user_id}")
    
    # Main menu navigation
    if data == "back":
        await start(update, context)
        return
    
    # ==================== VIEW SUBMENU ====================
    elif data == "view":
        keyboard = [
            [InlineKeyboardButton("⏳ Pending Applicants", callback_data="view_pending")],
            [InlineKeyboardButton("✅ Done Applicants", callback_data="view_done")],
            [InlineKeyboardButton("📦 Archived Applicants", callback_data="view_archived")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]
        ]
        await query.message.edit_text(
            "📋 *View Applicants*\n\nSelect a category:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "view_pending":
        try:
            result = await asyncio.to_thread(
                lambda: supabase.table("applications")
                .select("alias_email, first_name, last_name, whatsapp")
                .eq("payment", "pending")
                .execute()
            )
            users = result.data if result.data else []
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="view")]]
            
            if not users:
                await query.message.edit_text(
                    "⏳ *Pending Applicants*\n\nNo pending applicants found.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                message = "⏳ *Pending Applicants:*\n\n" + "\n".join(
                    [f"• {u['first_name']} {u['last_name']}\n  📧 `{u['alias_email']}`\n  📱 {u.get('whatsapp', 'N/A')}\n" 
                     for u in users]
                )
                await query.message.edit_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.message.edit_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="view")]])
            )
    
    elif data == "view_done":
        try:
            result = await asyncio.to_thread(
                lambda: supabase.table("applications")
                .select("alias_email, first_name, last_name, whatsapp")
                .eq("payment", "done")
                .execute()
            )
            users = result.data if result.data else []
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="view")]]
            
            if not users:
                await query.message.edit_text(
                    "✅ *Done Applicants*\n\nNo done applicants found.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                message = "✅ *Done Applicants:*\n\n" + "\n".join(
                    [f"• {u['first_name']} {u['last_name']}\n  📧 `{u['alias_email']}`\n  📱 {u.get('whatsapp', 'N/A')}\n" 
                     for u in users]
                )
                await query.message.edit_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.message.edit_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="view")]])
            )
    
    elif data == "view_archived":
        try:
            result = await asyncio.to_thread(
                lambda: supabase.table("applications_archive")
                .select("alias_email, first_name, last_name, whatsapp")
                .execute()
            )
            users = result.data if result.data else []
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="view")]]
            
            if not users:
                await query.message.edit_text(
                    "📦 *Archived Applicants*\n\nNo archived applicants found.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            else:
                message = "📦 *Archived Applicants:*\n\n" + "\n".join(
                    [f"• {u['first_name']} {u['last_name']}\n  📧 `{u['alias_email']}`\n  📱 {u.get('whatsapp', 'N/A')}\n" 
                     for u in users]
                )
                await query.message.edit_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.message.edit_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="view")]])
            )
    
    # ==================== PAYMENT SUBMENU ====================
    elif data == "payment":
        keyboard = [
            [InlineKeyboardButton("✅ Mark as Done", callback_data="pay_done")],
            [InlineKeyboardButton("⏳ Mark as Pending", callback_data="pay_pending")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]
        ]
        await query.message.edit_text(
            "💰 *Payment Management*\n\nSelect an action:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "pay_done":
        user_states[user_id] = {"action": "mark_done"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="payment")]]
        await query.message.edit_text(
            "✅ *Mark Payment as Done*\n\nSend the applicant's alias email:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "pay_pending":
        user_states[user_id] = {"action": "mark_pending"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="payment")]]
        await query.message.edit_text(
            "⏳ *Mark Payment as Pending*\n\nSend the applicant's alias email:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ==================== SUBSCRIPTION SUBMENU ====================
    elif data == "subscription":
        keyboard = [
            [InlineKeyboardButton("📅 Set Subscription Date", callback_data="sub_set")],
            [InlineKeyboardButton("➕ Extend Subscription", callback_data="sub_extend")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]
        ]
        await query.message.edit_text(
            "📅 *Subscription Management*\n\nSelect an action:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "sub_set":
        user_states[user_id] = {"action": "set_sub", "step": "email"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="subscription")]]
        await query.message.edit_text(
            "📅 *Set Subscription Date*\n\nSend the applicant's alias email:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "sub_extend":
        user_states[user_id] = {"action": "extend_sub", "step": "email"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="subscription")]]
        await query.message.edit_text(
            "➕ *Extend Subscription*\n\nSend the applicant's alias email:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ==================== ARCHIVE SUBMENU ====================
    elif data == "archive":
        keyboard = [
            [InlineKeyboardButton("📦 Archive Applicant", callback_data="arch_archive")],
            [InlineKeyboardButton("♻️ Restore Applicant", callback_data="arch_restore")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]
        ]
        await query.message.edit_text(
            "🗄️ *Archive Management*\n\nSelect an action:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "arch_archive":
        user_states[user_id] = {"action": "archive"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="archive")]]
        await query.message.edit_text(
            "📦 *Archive Applicant*\n\nSend the applicant's alias email:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "arch_restore":
        user_states[user_id] = {"action": "restore"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="archive")]]
        await query.message.edit_text(
            "♻️ *Restore Applicant*\n\nSend the applicant's alias email:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ==================== FIND APPLICANT ====================
    elif data == "find":
        user_states[user_id] = {"action": "find"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back")]]
        await query.message.edit_text(
            "🔍 *Find Applicant*\n\nSend the applicant's alias email:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ==================== STATISTICS ====================
    elif data == "stats":
        try:
            pending = await asyncio.to_thread(
                lambda: supabase.table("applications")
                .select("id", count="exact")
                .eq("payment", "pending")
                .execute().count
            )
            
            done = await asyncio.to_thread(
                lambda: supabase.table("applications")
                .select("id", count="exact")
                .eq("payment", "done")
                .execute().count
            )
            
            try:
                archived = await asyncio.to_thread(
                    lambda: supabase.table("applications_archive")
                    .select("id", count="exact")
                    .execute().count
                )
            except:
                archived = 0
            
            total = pending + done
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]]
            await query.message.edit_text(
                f"📊 *Statistics*\n\n"
                f"⏳ Pending: {pending}\n"
                f"✅ Done: {done}\n"
                f"📦 Archived: {archived}\n"
                f"➖➖➖➖➖➖➖\n"
                f"📈 Total Active: {total}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.message.edit_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
            )


# ==================== TEXT INPUT HANDLER ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for multi-step operations"""
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    action = state.get("action")
    
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Find applicant
    if action == "find":
        await find_applicant_details(update, text)
        del user_states[user_id]
    
    # Mark payment done
    elif action == "mark_done":
        try:
            await asyncio.to_thread(
                lambda: supabase.table("applications")
                .update({"payment": "done"})
                .eq("alias_email", text)
                .execute()
            )
            await update.message.reply_text(
                f"✅ Payment marked as *done* for:\n`{text}`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=reply_markup)
        del user_states[user_id]
    
    # Mark payment pending
    elif action == "mark_pending":
        try:
            await asyncio.to_thread(
                lambda: supabase.table("applications")
                .update({"payment": "pending"})
                .eq("alias_email", text)
                .execute()
            )
            await update.message.reply_text(
                f"⏳ Payment marked as *pending* for:\n`{text}`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=reply_markup)
        del user_states[user_id]
    
    # Set subscription - email step
    elif action == "set_sub" and state.get("step") == "email":
        user_states[user_id] = {"action": "set_sub", "step": "date", "email": text}
        await update.message.reply_text(
            f"📅 Email: `{text}`\n\nNow send the subscription expiration date (YYYY-MM-DD):",
            parse_mode='Markdown'
        )
    
    # Set subscription - date step
    elif action == "set_sub" and state.get("step") == "date":
        email = state.get("email")
        try:
            await asyncio.to_thread(
                lambda: supabase.table("applications")
                .update({"subscription_expiration": text})
                .eq("alias_email", email)
                .execute()
            )
            await update.message.reply_text(
                f"✅ Subscription set for:\n`{email}`\nUntil: *{text}*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=reply_markup)
        del user_states[user_id]
    
    # Extend subscription - email step
    elif action == "extend_sub" and state.get("step") == "email":
        user_states[user_id] = {"action": "extend_sub", "step": "days", "email": text}
        await update.message.reply_text(
            f"➕ Email: `{text}`\n\nNow send the number of days to extend:",
            parse_mode='Markdown'
        )
    
    # Extend subscription - days step
    elif action == "extend_sub" and state.get("step") == "days":
        email = state.get("email")
        try:
            days = int(text)
            result = await asyncio.to_thread(
                lambda: supabase.table("applications")
                .select("subscription_expiration")
                .eq("alias_email", email)
                .execute()
            )
            
            if not result.data:
                await update.message.reply_text(
                    f"❌ No applicant found with email:\n`{email}`", 
                    reply_markup=reply_markup, 
                    parse_mode='Markdown'
                )
            else:
                current_exp = datetime.strptime(result.data[0]["subscription_expiration"], "%Y-%m-%d")
                new_exp = (current_exp + timedelta(days=days)).date()
                
                await asyncio.to_thread(
                    lambda: supabase.table("applications")
                    .update({"subscription_expiration": new_exp.isoformat()})
                    .eq("alias_email", email)
                    .execute()
                )
                
                await update.message.reply_text(
                    f"✅ Subscription extended for:\n`{email}`\nNew expiration: *{new_exp}*\n(+{days} days)",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid number. Please send a valid number of days.", 
                reply_markup=reply_markup
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=reply_markup)
        del user_states[user_id]
    
    # Archive
    elif action == "archive":
        try:
            result = await asyncio.to_thread(
                lambda: supabase.table("applications")
                .select("*")
                .eq("alias_email", text)
                .execute()
            )
            
            if not result.data:
                await update.message.reply_text(
                    f"❌ No applicant found with email:\n`{text}`", 
                    reply_markup=reply_markup, 
                    parse_mode='Markdown'
                )
            else:
                await asyncio.to_thread(
                    lambda: supabase.table("applications_archive")
                    .insert(result.data)
                    .execute()
                )
                await asyncio.to_thread(
                    lambda: supabase.table("applications")
                    .delete()
                    .eq("alias_email", text)
                    .execute()
                )
                await update.message.reply_text(
                    f"✅ Applicant archived:\n`{text}`",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=reply_markup)
        del user_states[user_id]
    
    # Restore
    elif action == "restore":
        try:
            result = await asyncio.to_thread(
                lambda: supabase.table("applications_archive")
                .select("*")
                .eq("alias_email", text)
                .execute()
            )
            
            if not result.data:
                await update.message.reply_text(
                    f"❌ No archived applicant found with email:\n`{text}`", 
                    reply_markup=reply_markup, 
                    parse_mode='Markdown'
                )
            else:
                await asyncio.to_thread(
                    lambda: supabase.table("applications")
                    .insert(result.data)
                    .execute()
                )
                await asyncio.to_thread(
                    lambda: supabase.table("applications_archive")
                    .delete()
                    .eq("alias_email", text)
                    .execute()
                )
                await update.message.reply_text(
                    f"✅ Applicant restored:\n`{text}`",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=reply_markup)
        del user_states[user_id]


# ==================== FIND APPLICANT DETAILS ====================

async def find_applicant_details(update: Update, alias_email: str):
    """Show full applicant details"""
    try:
        result_main = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("*")
            .eq("alias_email", alias_email)
            .execute()
        )
        result_archive = await asyncio.to_thread(
            lambda: supabase.table("applications_archive")
            .select("*")
            .eq("alias_email", alias_email)
            .execute()
        )
        
        applicant = (result_main.data or []) + (result_archive.data or [])
        
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if not applicant:
            await update.message.reply_text(
                f"❌ No applicant found with email:\n`{alias_email}`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        a = applicant[0]
        
        # Header
        await update.message.reply_text(
            f"🚨 *APPLICANT DETAILS*\n\n"
            f"👤 {a.get('first_name', '-')} {a.get('last_name', '-')}\n"
            f"📧 `{a.get('alias_email', '-')}`",
            parse_mode='Markdown'
        )
        
        # CV
        await send_file_from_storage(update, a.get("cv_url"), "cv", "📄 CV")
        
        # Contact info
        await update.message.reply_text(
            f"📞 *Contact Information*\n\n"
            f"Name: {a.get('first_name','-')} {a.get('last_name','-')}\n"
            f"Email: {a.get('email','-')}\n"
            f"WhatsApp: {a.get('whatsapp','-')}\n"
            f"LinkedIn: {a.get('linkedin','-')}",
            parse_mode='Markdown'
        )
        
        # Compensation
        await update.message.reply_text(
            f"💰 *Compensation Details*\n\n"
            f"Expected Salary: {a.get('expected_salary_currency','-')} {a.get('expected_salary','-')}\n"
            f"Current Salary: {a.get('expected_salary_currency','-')} {a.get('current_salary','-')}\n"
            f"Payment Status: {a.get('payment','-')}",
            parse_mode='Markdown'
        )
        
        # Profile picture
        await send_file_from_storage(update, a.get("picture_url"), "pictures", "📸 Profile Picture")
        
        await update.message.reply_text("✅ All details sent!", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error finding applicant: {e}")
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back")]]
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ==================== MAIN ====================

def main():
    print("=" * 50)
    print("🤖 STARTING BOT")
    print("=" * 50)
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers - ORDER MATTERS!
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Bot started!")
    print("📱 Send /start to use the menu")
    
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()