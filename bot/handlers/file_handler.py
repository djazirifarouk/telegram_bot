import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler
from bot.keyboards.menus import get_home_button, get_continue_or_home_keyboard
from bot.handlers.edit import handle_recommendation_menu, handle_recommendation_remove
from database.queries import (
    upload_file_to_storage,
    delete_file_from_storage,
    update_applicant,
    get_applicant
)
from utils.state_manager import state_manager

logger = logging.getLogger(__name__)


def escape_markdown(text: str) -> str:
    """Escape special characters for Markdown."""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads (CV)."""
    user_id = update.message.from_user.id
    state = state_manager.get_state(user_id)
    
    if not state or state.get("step") != "upload_file" or state.get("file_type") != "cv":
        return
    
    document = update.message.document
    
    # Validate file type
    allowed_extensions = ['.pdf', '.doc', '.docx']
    filename = document.file_name
    
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        await update.message.reply_text(
            "❌ Invalid file type. Please send a PDF, DOC, or DOCX file."
        )
        return
    
    processing_msg = await update.message.reply_text("⏳ Uploading CV...")
    
    try:
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()
        
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]
        
        applicant = await get_applicant(lookup_field, lookup_value)
        if not applicant:
            await processing_msg.edit_text("❌ Applicant not found.")
            state_manager.clear_state(user_id)
            return
        
        old_cv_url = applicant.get("cv_url")
        if old_cv_url:
            await delete_file_from_storage(old_cv_url, "cv")
        
        new_cv_url = await upload_file_to_storage(bytes(file_bytes), filename, "cv")
        
        if not new_cv_url:
            await processing_msg.edit_text("❌ Error uploading CV. Please try again.")
            return
        
        success = await update_applicant(lookup_field, lookup_value, {"cv_url": new_cv_url})
        
        if success:
            await processing_msg.edit_text(
                "✅ CV updated successfully!",
                reply_markup=get_continue_or_home_keyboard()
            )
            # DON'T clear state
        else:
            await processing_msg.edit_text(
                "❌ Error updating database. Please try again.",
                reply_markup=get_home_button()
            )
            state_manager.clear_state(user_id)
        
    except Exception as e:
        logger.error(f"Error handling CV upload: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"❌ Error uploading CV. Please try again.",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)


async def handle_photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads (profile picture)."""
    user_id = update.message.from_user.id
    state = state_manager.get_state(user_id)
    
    if not state or state.get("step") != "upload_file" or state.get("file_type") != "picture":
        return
    
    photo = update.message.photo[-1]
    processing_msg = await update.message.reply_text("⏳ Uploading profile picture...")
    
    try:
        file = await context.bot.get_file(photo.file_id)
        file_bytes = await file.download_as_bytearray()
        
        filename = f"profile_{user_id}.jpg"
        
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]
        
        applicant = await get_applicant(lookup_field, lookup_value)
        if not applicant:
            await processing_msg.edit_text("❌ Applicant not found.")
            state_manager.clear_state(user_id)
            return
        
        old_picture_url = applicant.get("picture_url")
        if old_picture_url:
            await delete_file_from_storage(old_picture_url, "pictures")
        
        new_picture_url = await upload_file_to_storage(bytes(file_bytes), filename, "pictures")
        
        if not new_picture_url:
            await processing_msg.edit_text("❌ Error uploading picture. Please try again.")
            return
        
        success = await update_applicant(lookup_field, lookup_value, {"picture_url": new_picture_url})
        
        if success:
            await processing_msg.edit_text(
                "✅ Profile picture updated successfully!",
                reply_markup=get_continue_or_home_keyboard()
            )
            # DON'T clear state
        else:
            await processing_msg.edit_text(
                "❌ Error updating database. Please try again.",
                reply_markup=get_home_button()
            )
            state_manager.clear_state(user_id)
        
    except Exception as e:
        logger.error(f"Error handling photo upload: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"❌ Error uploading picture. Please try again.",
            reply_markup=get_home_button()
        )
        state_manager.clear_state(user_id)


async def handle_recommendation_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle recommendation letter uploads."""
    user_id = update.message.from_user.id
    state = state_manager.get_state(user_id)
    
    if not state or state.get("step") != "upload_file" or state.get("file_type") != "recommendation":
        return
    
    document = update.message.document
    
    # Validate file type (PDF only)
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text("❌ Please upload a PDF file.")
        return
    
    processing_msg = await update.message.reply_text("⏳ Uploading recommendation letter...")
    
    try:
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()
        
        lookup_field = state["lookup_field"]
        lookup_value = state["lookup_value"]
        
        applicant = await get_applicant(lookup_field, lookup_value)
        if not applicant:
            await processing_msg.edit_text("❌ Applicant not found.")
            state_manager.clear_state(user_id)
            return
        
        # Upload to storage
        from database.queries import upload_file_to_storage
        new_letter_url = await upload_file_to_storage(bytes(file_bytes), document.file_name, "letters")
        
        if not new_letter_url:
            await processing_msg.edit_text("❌ Error uploading letter.")
            return
        
        # Add to existing letters
        current_letters = applicant.get("recommendation_url", [])
        if not isinstance(current_letters, list):
            current_letters = []
        current_letters.append(new_letter_url)
        
        success = await update_applicant(lookup_field, lookup_value, {"recommendation_url": current_letters})
        
        if success:
            from bot.keyboards.menus import get_continue_or_home_keyboard
            await processing_msg.edit_text(
                f"✅ Recommendation letter uploaded!\n\nTotal: {len(current_letters)} letter(s)",
                reply_markup=get_continue_or_home_keyboard()
            )
            # Refresh state
            applicant = await get_applicant(lookup_field, lookup_value)
            state_manager.update_state(user_id, {"applicant": applicant})
        else:
            await processing_msg.edit_text("❌ Error saving to database.")
            state_manager.clear_state(user_id)
        
    except Exception as e:
        logger.error(f"Error uploading recommendation: {e}", exc_info=True)
        await processing_msg.edit_text("❌ Error uploading letter.")
        state_manager.clear_state(user_id)


def register_file_handlers(application):
    """Register file upload handlers."""
    # Document handler (for CV) - Register before text handler
    application.add_handler(
        MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_document_upload),
        group=0
    )
    
    # Photo handler (for profile picture) - Register before text handler
    application.add_handler(
        MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo_upload),
        group=0
    )

    application.add_handler(CallbackQueryHandler(handle_recommendation_menu, pattern="^rec:"))
    application.add_handler(CallbackQueryHandler(handle_recommendation_remove, pattern="^rec_rm:"))

    
    logger.info("✅ File upload handlers registered")