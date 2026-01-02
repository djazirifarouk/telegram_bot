import os
import io
import asyncio
import ast
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from supabase import create_client

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Command handlers ---
async def all_pending_applicants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all applicants whose payment is pending"""
    data = supabase.table("applications")\
        .select("alias_email, first_name, last_name, whatsapp")\
        .eq("payment", "pending")\
        .execute()
    users = data.data if data.data else []
    if not users:
        await update.message.reply_text("No pending users found.")
        return
    message = "\n".join([f"{u['first_name']} {u['last_name']} - {u['alias_email']} - {u['whatsapp']}" for u in users])
    await update.message.reply_text(f"Pending applicants:\n{message}")


async def all_done_applicants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all applicants whose payment is done"""
    data = supabase.table("applications").select("alias_email, first_name, last_name, whatsapp").eq("payment", "done").execute()
    applicants = data.data or []
    if not applicants:
        await update.message.reply_text("No applicants with done payment found.")
        return
    message = "\n".join([f"{a['first_name']} {a['last_name']} - {a['alias_email']} - {a['whatsapp']}" for a in applicants])
    await update.message.reply_text(f"Done applicants:\n{message}")


async def all_archived_applicants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all archived applicants"""
    data = supabase.table("applications_archive").select("alias_email, first_name, last_name, whatsapp").execute()
    applicants = data.data or []
    if not applicants:
        await update.message.reply_text("No archived applicants found.")
        return
    message = "\n".join([f"{a['first_name']} {a['last_name']} - {a['alias_email']} - {a['whatsapp']}" for a in applicants])
    await update.message.reply_text(f"Archived applicants:\n{message}")


def chunk_text(text: str, chunk_size: int = 4000):
    """Split text into Telegram-safe chunks"""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


async def send_file_from_storage(update: Update, file_url: str, bucket: str, caption: str):
    """Download file from Supabase Storage and send to Telegram"""
    if not file_url:
        await update.message.reply_text(f"No {caption} provided.")
        return

    try:
        # Extract just the file name
        import urllib.parse
        path = urllib.parse.urlparse(file_url).path.split('/')[-1]

        # Download file in a thread to avoid blocking
        file_bytes = await asyncio.to_thread(lambda: supabase.storage.from_(bucket).download(path))

        file_obj = io.BytesIO(file_bytes)
        file_obj.name = path  # Telegram requires a name for files

        await update.message.reply_document(document=file_obj, caption=caption)
    except Exception as e:
        await update.message.reply_text(f"Failed to download {caption}: {e}")


# ------------------ Main Function ------------------
async def find_applicant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show full details of a specific applicant with attached files"""
    if not context.args:
        await update.message.reply_text("Usage: /find_applicant <alias_email>")
        return

    alias_email = context.args[0]

    # Fetch applicant from main and archive tables
    data_main = supabase.table("applications").select("*").eq("alias_email", alias_email).execute()
    data_archive = supabase.table("applications_archive").select("*").eq("alias_email", alias_email).execute()
    applicant = (data_main.data or []) + (data_archive.data or [])

    if not applicant:
        await update.message.reply_text(f"No applicant found with alias_email: {alias_email}")
        return

    a = applicant[0]

    # ------------------ Send files ------------------
    await send_file_from_storage(update, a.get("picture_url"), "pictures", "Profile Picture")
    await send_file_from_storage(update, a.get("cv_url"), "cv", "CV")

    # Recommendation letters
    letters_urls = a.get("recommendation_url", [])
    if isinstance(letters_urls, str):
        try:
            letters_urls = ast.literal_eval(letters_urls)
        except Exception:
            letters_urls = []

    for i, letter_url in enumerate(letters_urls, start=1):
        if letter_url:
            await send_file_from_storage(update, letter_url, "letters", f"Recommendation Letter {i}")

    # ------------------ Prepare text sections ------------------
    sections = []

    # Personal Info
    personal_fields = ["first_name", "last_name", "email", "alias_email", "whatsapp", "linkedin", "twitter", "website"]
    personal_info = "\n".join([f"{f.replace('_', ' ').title()}: {a.get(f, '-')}" for f in personal_fields])
    sections.append(f"📌 Personal Info:\n{personal_info}")

    # Address Info
    address_fields = ["street", "building", "apartment", "city", "zip", "residency_country"]
    address_info = "\n".join([f"{f.replace('_', ' ').title()}: {a.get(f, '-')}" for f in address_fields])
    sections.append(f"🏠 Address Info:\n{address_info}")

    # Work Experience
    roles = a.get("roles", [])
    if roles:
        msg = "💼 Work Experience:\n"
        for r in roles:
            msg += f"- {r.get('title', '-')}, {r.get('company', '-')}, {r.get('location', '-')}\n"
            msg += f"  {r.get('start', '-')}-{r.get('end', '-')}, Current: {r.get('current', False)}\n"
            msg += f"  Description: {r.get('description', '-')}\n"
        sections.append(msg)

    # Education
    education = a.get("education", [])
    if education:
        msg = "🎓 Education:\n"
        for e in education:
            msg += f"- {e.get('school', '-')}, {e.get('degree', '-')}, {e.get('field', '-')}, {e.get('start', '-')}-{e.get('end', '-')}\n"
        sections.append(msg)

    # Certificates
    certificates = a.get("certificates", [])
    if certificates:
        msg = "📜 Certificates:\n"
        for c in certificates:
            msg += f"- {c.get('name', '-')}, Number: {c.get('number', '-')}, {c.get('start', '-')}-{c.get('end', '-')}\n"
        sections.append(msg)

    # Languages
    languages = a.get("languages", [])
    if languages:
        msg = "🗣 Languages:\n"
        for l in languages:
            msg += f"- {l.get('language', '-')}: {l.get('proficiency', '-')}\n"
        sections.append(msg)

    # Skills & Other Info
    skills = ", ".join(a.get("skills", [])) or "-"

    # Country Preference
    country_pref_raw = a.get("country_preference", [])
    if isinstance(country_pref_raw, str):
        try:
            country_pref_list = ast.literal_eval(country_pref_raw)
        except Exception:
            country_pref_list = []
    else:
        country_pref_list = country_pref_raw
    country_pref = ", ".join(country_pref_list) or "-"

    payment = a.get("payment", "-")
    subscription = a.get("subscription_expiration", "-")

    msg = f"⚡ Skills: {skills}\n🌍 Country Preference: {country_pref}\n💳 Payment: {payment}\n📅 Subscription Expiration: {subscription}"
    sections.append(msg)

    # ------------------ Send all sections safely ------------------
    for section in sections:
        for chunk in chunk_text(section):
            try:
                await update.message.reply_text(chunk)
            except Exception as e:
                # Prevent bot from crashing if Telegram times out
                print(f"Failed to send section: {e}")
async def mark_payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark an applicant's payment as done"""
    if not context.args:
        await update.message.reply_text("Usage: /mark_payment_done <alias_email>")
        return
    alias_email = context.args[0]
    supabase.table("applications").update({"payment": "done"}).eq("alias_email", alias_email).execute()
    await update.message.reply_text(f"Payment marked as done for {alias_email}")


async def mark_payment_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Revert an applicant's payment to pending"""
    if not context.args:
        await update.message.reply_text("Usage: /mark_payment_pending <alias_email>")
        return
    alias_email = context.args[0]
    supabase.table("applications").update({"payment": "pending"}).eq("alias_email", alias_email).execute()
    await update.message.reply_text(f"Payment marked as pending for {alias_email}")


async def set_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set subscription expiration date"""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /set_subscription <alias_email> <YYYY-MM-DD>")
        return
    alias_email, date_str = context.args[0], context.args[1]
    supabase.table("applications").update({"subscription_expiration": date_str}).eq("alias_email", alias_email).execute()
    await update.message.reply_text(f"Subscription set for {alias_email} until {date_str}")


async def extend_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Extend subscription by N days"""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /extend_subscription <alias_email> <days>")
        return
    alias_email, days = context.args[0], int(context.args[1])
    data = supabase.table("applications").select("subscription_expiration").eq("alias_email", alias_email).execute()
    if not data.data:
        await update.message.reply_text(f"No applicant found with alias_email: {alias_email}")
        return
    current_exp = datetime.strptime(data.data[0]["subscription_expiration"], "%Y-%m-%d")
    new_exp = (current_exp + timedelta(days=days)).date()
    supabase.table("applications").update({"subscription_expiration": new_exp.isoformat()}).eq("alias_email", alias_email).execute()
    await update.message.reply_text(f"Subscription extended for {alias_email} until {new_exp}")


async def archive_applicant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Move an applicant to archive table"""
    if not context.args:
        await update.message.reply_text("Usage: /archive_applicant <alias_email>")
        return
    alias_email = context.args[0]
    data = supabase.table("applications").select("*").eq("alias_email", alias_email).execute()
    if not data.data:
        await update.message.reply_text(f"No applicant found with alias_email: {alias_email}")
        return
    supabase.table("applications_archive").insert(data.data).execute()
    supabase.table("applications").delete().eq("alias_email", alias_email).execute()
    await update.message.reply_text(f"Applicant {alias_email} archived successfully")


async def restore_applicant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restore an archived applicant"""
    if not context.args:
        await update.message.reply_text("Usage: /restore_applicant <alias_email>")
        return
    alias_email = context.args[0]
    data = supabase.table("applications_archive").select("*").eq("alias_email", alias_email).execute()
    if not data.data:
        await update.message.reply_text(f"No archived applicant found with alias_email: {alias_email}")
        return
    supabase.table("applications").insert(data.data).execute()
    supabase.table("applications_archive").delete().eq("alias_email", alias_email).execute()
    await update.message.reply_text(f"Applicant {alias_email} restored successfully")


async def applicant_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show counts of pending, done, and archived applicants"""
    pending = supabase.table("applications").select("id", count="exact").eq("payment", "pending").execute().count
    done = supabase.table("applications").select("id", count="exact").eq("payment", "done").execute().count
    archived = supabase.table("applications_archive").select("id", count="exact").execute().count
    await update.message.reply_text(f"Applicant stats:\nPending: {pending}\nDone: {done}\nArchived: {archived}")


async def main():
    await app.start()
    print("Bot started...")
    await app.updater.start_polling()
    await asyncio.Event().wait()  # Keep the bot running

# -------------------- Main --------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Command Handlers
    app.add_handler(CommandHandler("all_pending_applicants", all_pending_applicants))
    app.add_handler(CommandHandler("all_done_applicants", all_done_applicants))
    app.add_handler(CommandHandler("all_archived_applicants", all_archived_applicants))
    app.add_handler(CommandHandler("find_applicant", find_applicant))
    app.add_handler(CommandHandler("mark_payment_done", mark_payment_done))
    app.add_handler(CommandHandler("mark_payment_pending", mark_payment_pending))
    app.add_handler(CommandHandler("set_subscription", set_subscription))
    app.add_handler(CommandHandler("extend_subscription", extend_subscription))
    app.add_handler(CommandHandler("archive_applicant", archive_applicant))
    app.add_handler(CommandHandler("restore_applicant", restore_applicant))
    app.add_handler(CommandHandler("applicant_stats", applicant_stats))
    
    print("Bot started. Waiting for commands...")
    app.run_polling()
    asyncio.run(main())
