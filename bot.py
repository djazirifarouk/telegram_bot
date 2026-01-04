import os
import io
import asyncio
import urllib.parse
import logging
from datetime import datetime, timedelta, date
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

# ==================== CONSTANTS ====================
EDITABLE_FIELDS = {
    "first_name": "First Name",
    "last_name": "Last Name",
    "email": "Personal Email",
    "whatsapp": "WhatsApp",
    "application_plan": "Application Plan",
    "roles": "Roles",
    "education": "Education",
    "skills": "Skills",
    "languages": "Languages",
    "certificates": "Certificates",
}

APPLICATION_PLAN_OPTIONS = ["Casual", "Normal", "Intense"]

LANGUAGE_PROFICIENCY_OPTIONS = [
    "A0 Starter",
    "A1 Beginner",
    "A2 Elementary",
    "B1 Intermediate",
    "B2 Upper Intermediate",
    "C1 Advanced",
    "C2 Mastery"
]

NESTED_FIELD_STRUCTURES = {
    "roles": {
        "fields": ["title", "company", "location", "start", "end", "current", "description"],
        "labels": {
            "title": "Title",
            "company": "Company",
            "location": "Location",
            "start": "Start Date (YYYY-MM)",
            "end": "End Date (YYYY-MM)",
            "current": "Currently Working",
            "description": "Description"
        },
        "types": {"current": "boolean"}
    },
    "education": {
        "fields": ["degree", "field", "school", "start", "end"],
        "labels": {
            "degree": "Degree",
            "field": "Field of Study",
            "school": "School/University",
            "start": "Start Date (YYYY-MM)",
            "end": "End Date (YYYY-MM)"
        }
    },
    "certificates": {
        "fields": ["name", "number", "start", "end"],
        "labels": {
            "name": "Course Name",
            "number": "Certificate Number",
            "start": "Start Date (YYYY-MM)",
            "end": "End Date (YYYY-MM)"
        }
    },
    "languages": {
        "fields": ["language", "proficiency"],
        "labels": {
            "language": "Language",
            "proficiency": "Proficiency Level"
        },
        "types": {"proficiency": "select"}
    }
}


# ==================== HELPERS ====================

def chunk_text(text: str, chunk_size: int = 4000):
    """Split text into Telegram-safe chunks"""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def resolve_lookup(value: str):
    value = value.strip()
    if "@" in value:
        return "alias_email", value.lower()
    digits = "".join(c for c in value if c.isdigit())
    return "whatsapp", digits


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


def format_nested_array(data_list, field_type):
    """Format nested array data for display"""
    if not data_list:
        return "None"
    
    structure = NESTED_FIELD_STRUCTURES.get(field_type, {})
    labels = structure.get("labels", {})
    
    result = []
    for idx, item in enumerate(data_list, 1):
        result.append(f"\n*{idx}.*")
        for key, value in item.items():
            label = labels.get(key, key.title())
            result.append(f"  • {label}: {value}")
    
    return "\n".join(result)


# ==================== MAIN MENU ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display main menu"""
    keyboard = [
        [InlineKeyboardButton("📋 View Applicants", callback_data="view")],
        [InlineKeyboardButton("💰 Payment Management", callback_data="payment")],
        [InlineKeyboardButton("📅 Subscription Management", callback_data="subscription")],
        [InlineKeyboardButton("✏️ Edit Applicant", callback_data="edit_applicant")],
        [InlineKeyboardButton("🗄️ Archive Management", callback_data="archive")],
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
            [InlineKeyboardButton("🔍 Find Applicant", callback_data="find")],
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
    
    # ==================== EDIT APPLICANT ====================
    elif data == "edit_applicant":
        user_states[user_id] = {
            "action": "edit_field",
            "step": "identify"
        }

        await query.message.edit_text(
            "✏️ *Edit Applicant*\n\n"
            "Send applicant **alias email** or **WhatsApp number**:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="back")]
            ]),
            parse_mode="Markdown"
        )

    elif data.startswith("edit_col:"):
        col = data.split("edit_col:")[1]
        state = user_states.get(user_id)
        if not state:
            return

        state.update({
            "step": "nested_menu" if col in NESTED_FIELD_STRUCTURES else "edit_value",
            "column": col
        })

        # Handle application_plan with menu
        if col == "application_plan":
            keyboard = [
                [InlineKeyboardButton(plan, callback_data=f"plan:{plan}")]
                for plan in APPLICATION_PLAN_OPTIONS
            ]
            keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
            
            await query.message.edit_text(
                "📝 *Select Application Plan:*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        # Handle nested fields (roles, education, certificates, languages)
        elif col in NESTED_FIELD_STRUCTURES:
            applicant = state.get("applicant", {})
            current_data = applicant.get(col, [])
            
            keyboard = [
                [InlineKeyboardButton("➕ Add New Entry", callback_data=f"nested_add:{col}")],
            ]
            
            # Show existing entries
            if current_data:
                await query.message.edit_text(
                    f"📋 *Current {EDITABLE_FIELDS[col]}:*\n{format_nested_array(current_data, col)}\n\n"
                    "Select an action:",
                    reply_markup=InlineKeyboardMarkup(keyboard + [
                        [InlineKeyboardButton("✏️ Edit Entry", callback_data=f"nested_edit:{col}")],
                        [InlineKeyboardButton("🗑️ Delete Entry", callback_data=f"nested_delete:{col}")],
                        [InlineKeyboardButton("🔙 Cancel", callback_data="back")]
                    ]),
                    parse_mode="Markdown"
                )
            else:
                keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
                await query.message.edit_text(
                    f"📋 *{EDITABLE_FIELDS[col]}*\n\nNo entries found. Add a new one?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        
        # Handle simple fields
        elif col in ["roles", "education", "languages", "skills"]:
            await query.message.edit_text(
                f"✏️ *Editing {EDITABLE_FIELDS[col]}*\n\n"
                "Send **full JSON array** to replace the value:",
                parse_mode="Markdown"
            )
        else:
            await query.message.edit_text(
                f"✏️ *Editing {EDITABLE_FIELDS[col]}*\n\n"
                "Send the new value:",
                parse_mode="Markdown"
            )

    # Handle application_plan selection
    elif data.startswith("plan:"):
        plan = data.split("plan:")[1]
        state = user_states.get(user_id)
        if not state:
            return
        
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]
        
        try:
            await asyncio.to_thread(
                lambda: supabase.table("applications")
                .update({"application_plan": plan})
                .eq(lookup_field, lookup_value)
                .execute()
            )
            
            await query.message.edit_text(
                f"✅ *Application Plan updated to: {plan}*",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                ]),
                parse_mode="Markdown"
            )
            del user_states[user_id]
        except Exception as e:
            await query.message.edit_text(f"❌ Error: {e}")

    # Handle nested field operations
    elif data.startswith("nested_add:"):
        field_type = data.split("nested_add:")[1]
        state = user_states.get(user_id)
        if not state:
            return
        
        state.update({
            "step": "nested_input",
            "nested_action": "add",
            "nested_type": field_type,
            "nested_data": {},
            "nested_field_index": 0
        })
        
        # Start collecting fields
        structure = NESTED_FIELD_STRUCTURES[field_type]
        first_field = structure["fields"][0]
        field_label = structure["labels"][first_field]
        
        # Check if it's a boolean or select field
        field_types = structure.get("types", {})
        if first_field in field_types:
            if field_types[first_field] == "boolean":
                keyboard = [
                    [InlineKeyboardButton("✅ True", callback_data=f"bool:true:{first_field}")],
                    [InlineKeyboardButton("❌ False", callback_data=f"bool:false:{first_field}")],
                    [InlineKeyboardButton("🔙 Cancel", callback_data="back")]
                ]
                await query.message.edit_text(
                    f"Select *{field_label}*:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return
            elif field_types[first_field] == "select" and first_field == "proficiency":
                keyboard = [
                    [InlineKeyboardButton(prof, callback_data=f"prof:{prof}")]
                    for prof in LANGUAGE_PROFICIENCY_OPTIONS
                ]
                keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
                await query.message.edit_text(
                    f"Select *{field_label}*:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return
        
        await query.message.edit_text(
            f"📝 Enter *{field_label}*:",
            parse_mode="Markdown"
        )

    elif data.startswith("nested_edit:"):
        field_type = data.split("nested_edit:")[1]
        state = user_states.get(user_id)
        if not state:
            return
        
        applicant = state.get("applicant", {})
        current_data = applicant.get(field_type, [])
        
        if not current_data:
            await query.message.edit_text("❌ No entries to edit.")
            return
        
        state.update({
            "step": "nested_select_entry",
            "nested_action": "edit",
            "nested_type": field_type
        })
        
        keyboard = [
            [InlineKeyboardButton(f"Entry {i+1}", callback_data=f"entry_select:{i}")]
            for i in range(len(current_data))
        ]
        keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
        
        await query.message.edit_text(
            f"Select entry to edit:\n{format_nested_array(current_data, field_type)}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("nested_delete:"):
        field_type = data.split("nested_delete:")[1]
        state = user_states.get(user_id)
        if not state:
            return
        
        applicant = state.get("applicant", {})
        current_data = applicant.get(field_type, [])
        
        if not current_data:
            await query.message.edit_text("❌ No entries to delete.")
            return
        
        state.update({
            "step": "nested_select_entry",
            "nested_action": "delete",
            "nested_type": field_type
        })
        
        keyboard = [
            [InlineKeyboardButton(f"Entry {i+1}", callback_data=f"entry_select:{i}")]
            for i in range(len(current_data))
        ]
        keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
        
        await query.message.edit_text(
            f"Select entry to delete:\n{format_nested_array(current_data, field_type)}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("entry_select:"):
        entry_index = int(data.split("entry_select:")[1])
        state = user_states.get(user_id)
        if not state:
            return
        
        nested_action = state.get("nested_action")
        field_type = state.get("nested_type")
        applicant = state.get("applicant", {})
        current_data = applicant.get(field_type, [])
        
        if nested_action == "delete":
            # Delete the entry
            lookup_field = state["lookup_field"]
            lookup_value = state["lookup_value"]
            
            current_data.pop(entry_index)
            
            try:
                await asyncio.to_thread(
                    lambda: supabase.table("applications")
                    .update({field_type: current_data})
                    .eq(lookup_field, lookup_value)
                    .execute()
                )
                
                await query.message.edit_text(
                    f"✅ *Entry deleted successfully!*",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                    ]),
                    parse_mode="Markdown"
                )
                del user_states[user_id]
            except Exception as e:
                await query.message.edit_text(f"❌ Error: {e}")
        
        elif nested_action == "edit":
            # Start editing the entry
            state.update({
                "step": "nested_input",
                "nested_entry_index": entry_index,
                "nested_data": current_data[entry_index].copy(),
                "nested_field_index": 0
            })
            
            structure = NESTED_FIELD_STRUCTURES[field_type]
            first_field = structure["fields"][0]
            field_label = structure["labels"][first_field]
            current_value = current_data[entry_index].get(first_field, "")
            
            # Check if it's a boolean or select field
            field_types = structure.get("types", {})
            if first_field in field_types:
                if field_types[first_field] == "boolean":
                    keyboard = [
                        [InlineKeyboardButton("✅ True", callback_data=f"bool:true:{first_field}")],
                        [InlineKeyboardButton("❌ False", callback_data=f"bool:false:{first_field}")],
                        [InlineKeyboardButton("🔙 Cancel", callback_data="back")]
                    ]
                    await query.message.edit_text(
                        f"Current: *{current_value}*\n\nSelect new *{field_label}*:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                    return
                elif field_types[first_field] == "select" and first_field == "proficiency":
                    keyboard = [
                        [InlineKeyboardButton(prof, callback_data=f"prof:{prof}")]
                        for prof in LANGUAGE_PROFICIENCY_OPTIONS
                    ]
                    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
                    await query.message.edit_text(
                        f"Current: *{current_value}*\n\nSelect new *{field_label}*:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                    return
            
            await query.message.edit_text(
                f"Current: *{current_value}*\n\nEnter new *{field_label}*:",
                parse_mode="Markdown"
            )

    # Handle boolean selections
    elif data.startswith("bool:"):
        _, value, field_name = data.split(":")
        bool_value = value == "true"
        
        state = user_states.get(user_id)
        if not state:
            return
        
        await process_nested_field_input(update, context, str(bool_value))

    # Handle proficiency selections
    elif data.startswith("prof:"):
        proficiency = data.split("prof:")[1]
        state = user_states.get(user_id)
        if not state:
            return
        
        await process_nested_field_input(update, context, proficiency)
    
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
            "✅ *Mark Payment as Done*\n\nSend the applicant's alias email or phone number:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "pay_pending":
        user_states[user_id] = {"action": "mark_pending"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="payment")]]
        await query.message.edit_text(
            "⏳ *Mark Payment as Pending*\n\nSend the applicant's alias email or phone number:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ==================== SUBSCRIPTION SUBMENU ====================
    elif data == "subscription":
        keyboard = [
            [InlineKeyboardButton("📅 Set Subscription Date", callback_data="sub_set")],
            [InlineKeyboardButton("➕ Extend Subscription", callback_data="sub_extend")],
            [InlineKeyboardButton("❌ Expired", callback_data="sub_expired")],
            [InlineKeyboardButton("⏳ Expiring Soon", callback_data="sub_soon")],
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
            "📅 *Set Subscription Date*\n\nSend the applicant's alias email or phone number:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "sub_extend":
        user_states[user_id] = {"action": "extend_sub", "step": "email"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="subscription")]]
        await query.message.edit_text(
            "➕ *Extend Subscription*\n\nSend the applicant's alias email or phone number:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "sub_expired":
        today_str = date.today().isoformat()
        response = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("alias_email, whatsapp, subscription_expiration")
            .lte("subscription_expiration", today_str)
            .execute()
        )
        expired = response.data or []
        msg = "⚠️ *Expired subscriptions:*\n\n" + \
            "\n".join([f"{u['alias_email']} | {u['whatsapp']} - {u['subscription_expiration']}" for u in expired]) \
            if expired else "No expired subscriptions today."
        await query.message.edit_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="subscription")]]))

    elif data == "sub_soon":
        today = date.today()
        soon = (today + timedelta(days=7)).isoformat()
        response = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("alias_email, whatsapp, subscription_expiration")
            .gt("subscription_expiration", today.isoformat())
            .lte("subscription_expiration", soon)
            .execute()
        )
        expiring = response.data or []
        msg = "⏳ *Subscriptions expiring in 7 days:*\n\n" + \
            "\n".join([f"{u['alias_email']} | {u['whatsapp']} - {u['subscription_expiration']}" for u in expiring]) \
            if expiring else "No subscriptions expiring in the next 7 days."
        await query.message.edit_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="subscription")]]))
    
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
            "📦 *Archive Applicant*\n\nSend the applicant's alias email or phone number:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "arch_restore":
        user_states[user_id] = {"action": "restore"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="archive")]]
        await query.message.edit_text(
            "♻️ *Restore Applicant*\n\nSend the applicant's alias email or phone number:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # ==================== FIND APPLICANT ====================
    elif data == "find":
        user_states[user_id] = {"action": "find"}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back")]]
        await query.message.edit_text(
            "🔍 *Find Applicant*\n\nSend the applicant's alias email or phone number:",
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

            plans = await asyncio.to_thread(
                lambda: supabase.rpc("get_applications_per_plan").execute()
            )
            plan_stats = "\n".join(
                [f"• {p['application_plan']}: {p['count']}" 
                for p in plans.data 
                if p["application_plan"]]
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back")]]
            await query.message.edit_text(
                f"📊 *Statistics*\n\n"
                f"⏳ Pending: {pending}\n"
                f"✅ Done: {done}\n"
                f"📦 Archived: {archived}\n\n"
                f"✒️ *Applicants per Plan*\n\n"
                f"{plan_stats or 'No plans found'}\n"
                f"➖➖➖➖➖➖➖\n"
                f"📈 Total Active: {total}\n",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.message.edit_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
            )


# ==================== NESTED FIELD INPUT PROCESSOR ====================

async def process_nested_field_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Process input for nested field creation/editing"""
    user_id = update.effective_user.id
    state = user_states.get(user_id)
    
    if not state or state.get("step") != "nested_input":
        return
    
    field_type = state["nested_type"]
    structure = NESTED_FIELD_STRUCTURES[field_type]
    fields = structure["fields"]
    labels = structure["labels"]
    field_types = structure.get("types", {})
    current_field_idx = state["nested_field_index"]
    current_field = fields[current_field_idx]
    
    # Store the input
    state["nested_data"][current_field] = text
    
    # Move to next field
    next_field_idx = current_field_idx + 1
    
    if next_field_idx < len(fields):
        # More fields to collect
        state["nested_field_index"] = next_field_idx
        next_field = fields[next_field_idx]
        next_label = labels[next_field]
        
        # Check if next field is boolean or select
        if next_field in field_types:
            if field_types[next_field] == "boolean":
                keyboard = [
                    [InlineKeyboardButton("✅ True", callback_data=f"bool:true:{next_field}")],
                    [InlineKeyboardButton("❌ False", callback_data=f"bool:false:{next_field}")],
                    [InlineKeyboardButton("🔙 Cancel", callback_data="back")]
                ]
                
                if update.callback_query:
                    await update.callback_query.message.edit_text(
                        f"Select *{next_label}*:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        f"Select *{next_label}*:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                return
            elif field_types[next_field] == "select" and next_field == "proficiency":
                keyboard = [
                    [InlineKeyboardButton(prof, callback_data=f"prof:{prof}")]
                    for prof in LANGUAGE_PROFICIENCY_OPTIONS
                ]
                keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])
                
                if update.callback_query:
                    await update.callback_query.message.edit_text(
                        f"Select *{next_label}*:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        f"Select *{next_label}*:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                return
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                f"📝 Enter *{next_label}*:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"📝 Enter *{next_label}*:",
                parse_mode="Markdown"
            )
    else:
        # All fields collected, save to database
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]
        nested_action = state["nested_action"]
        
        # Get current data
        result = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select(field_type)
            .eq(lookup_field, lookup_value)
            .execute()
        )
        
        if not result.data:
            if update.callback_query:
                await update.callback_query.message.edit_text("❌ Applicant not found.")
            else:
                await update.message.reply_text("❌ Applicant not found.")
            del user_states[user_id]
            return
        
        current_data = result.data[0].get(field_type, [])
        if not isinstance(current_data, list):
            current_data = []
        
        # Add or edit entry
        if nested_action == "add":
            current_data.append(state["nested_data"])
        elif nested_action == "edit":
            entry_index = state["nested_entry_index"]
            current_data[entry_index] = state["nested_data"]
        
        # Update database
        try:
            await asyncio.to_thread(
                lambda: supabase.table("applications")
                .update({field_type: current_data})
                .eq(lookup_field, lookup_value)
                .execute()
            )
            
            success_msg = f"✅ *{EDITABLE_FIELDS[field_type]} {'added' if nested_action == 'add' else 'updated'} successfully!*"
            
            if update.callback_query:
                await update.callback_query.message.edit_text(
                    success_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                    ]),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    success_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                    ]),
                    parse_mode="Markdown"
                )
            
            del user_states[user_id]
        except Exception as e:
            error_msg = f"❌ Error: {e}"
            if update.callback_query:
                await update.callback_query.message.edit_text(error_msg)
            else:
                await update.message.reply_text(error_msg)


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
            field, value = resolve_lookup(text)
            await asyncio.to_thread(
                lambda: supabase.table("applications")
                .update({"payment": "done"})
                .eq(field, value)
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
            field, value = resolve_lookup(text)
            await asyncio.to_thread(
                lambda: supabase.table("applications")
                .update({"payment": "pending"})
                .eq(field, value)
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
            field, value = resolve_lookup(email)
            await asyncio.to_thread(
                lambda: supabase.table("applications")
                .update({"subscription_expiration": text})
                .eq(field, value)
                .execute()
            )
            await update.message.reply_text(
                f"✅ Subscription set for:\n`{value}`\nUntil: *{text}*",
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
            field, value = resolve_lookup(email)
            days = int(text)
            result = await asyncio.to_thread(
                lambda: supabase.table("applications")
                .select("subscription_expiration")
                .eq(field, value)
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
                    .eq(field, value)
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

    # Edit field - identify applicant
    elif action == "edit_field" and state["step"] == "identify":
        field, value = resolve_lookup(text)

        result = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("*")
            .eq(field, value)
            .execute()
        )

        if not result.data:
            await update.message.reply_text("❌ Applicant not found.")
            del user_states[user_id]
            return

        user_states[user_id].update({
            "step": "choose_field",
            "lookup_field": field,
            "lookup_value": value,
            "applicant": result.data[0]
        })

        keyboard = [
            [InlineKeyboardButton(v, callback_data=f"edit_col:{k}")]
            for k, v in EDITABLE_FIELDS.items()
        ]
        keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="back")])

        await update.message.reply_text(
            "🧩 *Select field to edit:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # Edit simple field - receive value
    elif action == "edit_field" and state["step"] == "edit_value":
        col = state["column"]
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]

        try:
            # Parse JSON for array fields
            if col in ["roles", "education", "languages", "skills"]:
                import json
                new_value = json.loads(text)
            else:
                new_value = text

            await asyncio.to_thread(
                lambda: supabase.table("applications")
                .update({col: new_value})
                .eq(lookup_field, lookup_value)
                .execute()
            )

            await update.message.reply_text(
                f"✅ *Updated {EDITABLE_FIELDS[col]} successfully!*",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                ]),
                parse_mode="Markdown"
            )

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

        del user_states[user_id]
    
    # Handle nested field input
    elif action == "edit_field" and state.get("step") == "nested_input":
        await process_nested_field_input(update, context, text)
    
    # Archive
    elif action == "archive":
        try:
            field, value = resolve_lookup(text)
            result = await asyncio.to_thread(
                lambda: supabase.table("applications")
                .select("*")
                .eq(field, value)
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
                    .eq(field, value)
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
            field, value = resolve_lookup(text)
            result = await asyncio.to_thread(
                lambda: supabase.table("applications_archive")
                .select("*")
                .eq(field, value)
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
                    .eq(field, value)
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

async def find_applicant_details(update: Update, text: str):
    """Show full applicant details"""
    try:
        field, value = resolve_lookup(text)
        result_main = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("*")
            .eq(field, value)
            .execute()
        )
        result_archive = await asyncio.to_thread(
            lambda: supabase.table("applications_archive")
            .select("*")
            .eq(field, value)
            .execute()
        )
        
        applicant = (result_main.data or []) + (result_archive.data or [])
        
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if not applicant:
            await update.message.reply_text(
                f"❌ No applicant found with {field}:\n`{text}`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        a = applicant[0]
        
        # Header
        await update.message.reply_text(
            f"🚨 *APPLICANT DETAILS*\n\n"
            f"👤 {a.get('first_name', '-')} {a.get('last_name', '-')}\n"
            f"✒️ Plan: {a.get('application_plan', '-')}\n"
            f"📧 Alias: `{a.get('alias_email', '-')}`\n"
            f"📧 Personal email: `{a.get('email', '-')}`\n",
            parse_mode='Markdown'
        )

        # Search Preferences
        country_pref = a.get("country_preference")
        if isinstance(country_pref, list):
            country_text = ", ".join(country_pref) if country_pref else "-"
        else:
            country_text = country_pref or "-"
        await update.message.reply_text(
            f"🔎 *Search Preferences*\n\n"
            f"Applying for: `{a.get('apply_role', '-')}`\n"
            f"Search AI Accuracy: `{a.get('search_accuracy', '-')}`\n"
            f"Employment Type: `{a.get('employment_type', '-')}`\n"
            f"Country Preference: `{country_text}`",
            parse_mode="Markdown"
        )
        
        # CV
        await send_file_from_storage(update, a.get("cv_url"), "cv", "📄 CV")
        
        # Contact info
        await update.message.reply_text(
            f"📞 *Contact Information*\n\n"
            f"Name: {a.get('first_name','-')} {a.get('last_name','-')}\n"
            f"Email: {a.get('email','-')}\n"
            f"WhatsApp: {a.get('whatsapp','-')}\n"
            f"LinkedIn: {a.get('linkedin','-')}\n"
            f"X/Twitter: {a.get('twitter','-')}\n"
            f"GitHub: {a.get('github','-')}\n"
            f"Portfolio: {a.get('website','-')}",
            parse_mode='Markdown'
        )

        # Address info
        await update.message.reply_text(
            f"🏠 *Address Information*\n\n"
            f"Street: {a.get('street','-')}\n"
            f"Building No: {a.get('building','-')}\n"
            f"Apartment No: {a.get('apartment','-')}\n"
            f"City: {a.get('city','-')}\n"
            f"Country: {a.get('country','-')}\n"
            f"Zip Code: {a.get('zip','-')}",
            parse_mode='Markdown'
        )

        # Legalisation
        await update.message.reply_text(
            f"📝 *Legalisation*\n\n"
            f"Authorized Countries: {a.get('autorized_countries','-')}\n"
            f"Visa: {a.get('visa','-')}\n"
            f"Willing to relocation: {a.get('relocate','-')}\n"
            f"Total years of Experience: {a.get('experience','-')} years",
            parse_mode='Markdown'
        )
        
        # Roles
        roles = a.get("roles")
        if not roles:
            roles_text = "-"
        else:
            lines = []
            for r in roles:
                lines.append(
                    f"• *{r.get('title','-')}* at {r.get('company','-')}\n"
                    f"  📍 {r.get('location','-')}\n"
                    f"  🗓️ {r.get('start','-')} → "
                    f"{'Present' if r.get('current') else r.get('end','-')}\n"
                    f"  📝 {r.get('description','-')}"
                )
            roles_text = "\n\n".join(lines)

        await update.message.reply_text(
            f"🎯 *Roles*\n\n"
            f"{roles_text}",
            parse_mode="Markdown"
        )

        # Education
        education = a.get("education")
        if not education:
            education_text = "-"
        else:
            lines = []
            for e in education:
                lines.append(
                    f"• *{e.get('degree','-')}* — {e.get('field','-')}\n"
                    f"  🏫 {e.get('school','-')}\n"
                    f"  🗓️ {e.get('start','-')} → {e.get('end','-')}"
                )
            education_text = "\n\n".join(lines)

        await update.message.reply_text(
            f"🎓 *Education*\n\n"
            f"{education_text}",
            parse_mode="Markdown"
        )

        # Certificates
        certificates = a.get("certificates")
        if not certificates:
            certificates_text = "-"
        else:
            lines = []
            for c in certificates:
                lines.append(
                    f"• *{c.get('name','-')}*\n"
                    f"  🆔 {c.get('number','-')}\n"
                    f"  🗓️ {c.get('start','-')} → {c.get('end','-')}"
                )
            certificates_text = "\n\n".join(lines)

        await update.message.reply_text(
            f"📜 *Courses & Certificates*\n\n"
            f"{certificates_text}",
            parse_mode="Markdown"
        )

        # Languages
        languages = a.get("languages")
        if not languages:
            languages_text = "-"
        else:
            lines = []
            for l in languages:
                lines.append(
                    f"• *{l.get('language','-')}* — {l.get('proficiency','-')}"
                )
            languages_text = "\n".join(lines)

        await update.message.reply_text(
            f"🌍 *Languages*\n\n"
            f"{languages_text}",
            parse_mode="Markdown"
        )

        # Skills
        skills = a.get("skills")
        if isinstance(skills, list):
            skills_text = ", ".join(skills) if skills else "-"
        else:
            skills_text = skills or "-"
        await update.message.reply_text(
            f"🎯 *Skills*\n\n"
            f"{skills_text}",
            parse_mode="Markdown"
        )

        # Compensation
        await update.message.reply_text(
            f"💰 *Compensation Details*\n\n"
            f"Expected Salary: {a.get('expected_salary_currency','-')} {a.get('expected_salary','-')}\n"
            f"Current Salary: {a.get('expected_salary_currency','-')} {a.get('current_salary','-')}\n"
            f"Payment Status: {a.get('payment','-')}",
            parse_mode='Markdown'
        )

        # Achievements
        await update.message.reply_text(
            f"🏆 *Achievements*\n\n"
            f"{a.get('achievements','-')}",
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

    # Start bot
    print("✅ Bot started!")
    print("📱 Send /start to use the menu")
    
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()