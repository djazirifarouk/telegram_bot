import os
import ast
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from supabase import create_client

# ------------------ Load environment variables ------------------
load_dotenv()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------ Conversation states ------------------
SELECT_FIELD, ENTER_VALUE = range(2)

# ------------------ Fields that can be modified ------------------
MODIFIABLE_FIELDS = {
    "first_name": "First Name",
    "last_name": "Last Name",
    "email": "Email",
    "alias_email": "Alias Email",
    "whatsapp": "WhatsApp",
    "linkedin": "LinkedIn",
    "twitter": "X / Twitter",
    "website": "Website",
    "street": "Street",
    "building": "Building No",
    "apartment": "Apartment No",
    "residency_country": "Country of Residency",
    "city": "City",
    "zip": "ZIP Code",
    "years_of_experience": "Years of Experience",
    "expected_salary": "Expected Annual Salary",
    "current_salary": "Current Annual Salary",
    "notice_period": "Notice Period (days)",
    # Nested fields
    "roles": "Roles",
    "education": "Education",
    "certificates": "Certificates",
    "languages": "Languages",
    "skills": "Skills",
}

# ------------------ Start modification ------------------
async def modify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /modify <alias_email>")
        return ConversationHandler.END

    alias_email = context.args[0]
    context.user_data["alias_email"] = alias_email

    # Build menu keyboard in 3 columns with UNIQUE prefixes
    buttons = [
        InlineKeyboardButton(label, callback_data=f"modify_{field}")
        for field, label in MODIFIABLE_FIELDS.items()
    ]
    keyboard = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
    
    # Add cancel button
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="modify_cancel")])

    await update.message.reply_text(
        f"🛠️ Modifying applicant: `{alias_email}`\n\nSelect the field you want to modify:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_FIELD

# ------------------ User selects the field ------------------
async def select_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Remove the "modify_" prefix
    field = query.data.replace("modify_", "")
    
    # Handle cancel
    if field == "cancel":
        await query.edit_message_text("❌ Modification cancelled.")
        return ConversationHandler.END
    
    context.user_data["field"] = field
    label = MODIFIABLE_FIELDS.get(field, field)

    # Provide instructions based on field type
    instructions = f"✏️ Send the new value for **{label}**:"

    if field in ["roles", "education", "certificates", "languages"]:
        instructions += (
            "\n\n📌 For nested fields, send as a list of dictionaries in JSON format.\n"
            "Example:\n"
            '```\n[{"title": "Role Name", "company": "Company", "start": "2022", "end": "2023", "current": false}]\n```'
        )
    elif field == "skills":
        instructions += "\n\n📌 Send as comma-separated values.\nExample: Python, JavaScript, Docker"

    await query.edit_message_text(instructions, parse_mode="Markdown")
    return ENTER_VALUE

# ------------------ Apply the modification ------------------
async def apply_modification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alias_email = context.user_data["alias_email"]
    field = context.user_data["field"]
    new_value_raw = update.message.text.strip()

    # Format nested fields
    if field in ["roles", "education", "certificates", "languages"]:
        try:
            new_value = ast.literal_eval(new_value_raw)
            if not isinstance(new_value, list):
                raise ValueError()
        except Exception:
            await update.message.reply_text(
                "❌ Invalid format. Please send a valid list of dictionaries.\n"
                "Type /cancel to stop this operation."
            )
            return ENTER_VALUE
    elif field == "skills":
        new_value = [s.strip() for s in new_value_raw.split(",") if s.strip()]
    else:
        new_value = new_value_raw

    # Update main table first
    try:
        res_main = supabase.table("applications").update({field: new_value}).eq(
            "alias_email", alias_email
        ).execute()

        if res_main.data:
            table = "applications"
        else:
            # Fallback to archive
            res_archive = supabase.table("applications_archive").update({field: new_value}).eq(
                "alias_email", alias_email
            ).execute()

            if not res_archive.data:
                await update.message.reply_text("❌ Applicant not found.")
                return ConversationHandler.END

            table = "applications_archive"

        await update.message.reply_text(
            f"✅ **{MODIFIABLE_FIELDS.get(field, field)}** updated successfully in `{table}`.\n\n"
            f"Applicant: `{alias_email}`\n"
            f"Field: {MODIFIABLE_FIELDS.get(field, field)}\n"
            f"New value: {new_value if not isinstance(new_value, list) else 'List updated'}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error updating field: {str(e)}")

    return ConversationHandler.END

# ------------------ Cancel handler ------------------
async def cancel_modify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the modification process"""
    await update.message.reply_text("❌ Modification cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

# ------------------ Conversation Handler ------------------
modify_handler = ConversationHandler(
    entry_points=[CommandHandler("modify", modify)],
    states={
        SELECT_FIELD: [
            CallbackQueryHandler(select_field, pattern="^modify_")
        ],
        ENTER_VALUE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, apply_modification)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_modify)],
    per_message=False,  # False because we have MessageHandler (not just CallbackQueryHandler)
    per_chat=True,
    per_user=True,
    name="modify_conversation"
)