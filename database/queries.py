import asyncio
import io
from datetime import datetime
import urllib.parse
import urllib.parse
import logging
from typing import Optional, List, Dict, Any
from .supabase_client import supabase

logger = logging.getLogger(__name__)


async def get_applicant(field: str, value: str, table: str = "applications") -> Optional[Dict]:
    """
    Get applicant by field value.
    
    Args:
        field: Field name to search
        value: Value to search for
        table: Table name (applications or applications_archive)
        
    Returns:
        Applicant data or None
    """
    result = await asyncio.to_thread(
        lambda: supabase.table(table)
        .select("*")
        .eq(field, value)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_applicants_by_status(status: str) -> List[Dict]:
    """
    Get applicants by payment status.
    
    Args:
        status: Payment status (pending/done)
        
    Returns:
        List of applicants
    """
    result = await asyncio.to_thread(
        lambda: supabase.table("applications")
        .select("alias_email, first_name, last_name, whatsapp")
        .eq("payment", status)
        .execute()
    )
    return result.data if result.data else []


async def get_archived_applicants() -> List[Dict]:
    """Get all archived applicants."""
    result = await asyncio.to_thread(
        lambda: supabase.table("applications_archive")
        .select("alias_email, first_name, last_name, whatsapp")
        .execute()
    )
    return result.data if result.data else []


async def update_applicant(field: str, value: str, updates: Dict) -> bool:
    """
    Update applicant data.
    
    Args:
        field: Field to match
        value: Value to match
        updates: Dictionary of updates
        
    Returns:
        True if successful
    """
    try:
        await asyncio.to_thread(
            lambda: supabase.table("applications")
            .update(updates)
            .eq(field, value)
            .execute()
        )
        return True
    except Exception as e:
        logger.error(f"Error updating applicant: {e}")
        return False


async def archive_applicant(field: str, value: str) -> bool:
    """
    Archive an applicant.
    
    Args:
        field: Field to match
        value: Value to match
        
    Returns:
        True if successful
    """
    try:
        # Get applicant data
        result = await asyncio.to_thread(
            lambda: supabase.table("applications")
            .select("*")
            .eq(field, value)
            .execute()
        )
        
        if not result.data:
            return False
        
        # Insert into archive
        await asyncio.to_thread(
            lambda: supabase.table("applications_archive")
            .insert(result.data)
            .execute()
        )
        
        # Delete from main table
        await asyncio.to_thread(
            lambda: supabase.table("applications")
            .delete()
            .eq(field, value)
            .execute()
        )
        return True
    except Exception as e:
        logger.error(f"Error archiving applicant: {e}")
        return False


async def restore_applicant(field: str, value: str) -> bool:
    """
    Restore an archived applicant.
    
    Args:
        field: Field to match
        value: Value to match
        
    Returns:
        True if successful
    """
    try:
        # Get archived data
        result = await asyncio.to_thread(
            lambda: supabase.table("applications_archive")
            .select("*")
            .eq(field, value)
            .execute()
        )
        
        if not result.data:
            return False
        
        # Insert into main table
        await asyncio.to_thread(
            lambda: supabase.table("applications")
            .insert(result.data)
            .execute()
        )
        
        # Delete from archive
        await asyncio.to_thread(
            lambda: supabase.table("applications_archive")
            .delete()
            .eq(field, value)
            .execute()
        )
        return True
    except Exception as e:
        logger.error(f"Error restoring applicant: {e}")
        return False


async def get_statistics() -> Dict[str, Any]:
    """
    Get application statistics.
    
    Returns:
        Dictionary with statistics
    """
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
        
        plans = await asyncio.to_thread(
            lambda: supabase.rpc("get_applications_per_plan").execute()
        )
        
        return {
            "pending": pending,
            "done": done,
            "archived": archived,
            "total": pending + done,
            "plans": plans.data
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {
            "pending": 0,
            "done": 0,
            "archived": 0,
            "total": 0,
            "plans": []
        }


async def download_file_from_storage(file_url: str, bucket: str) -> Optional[io.BytesIO]:
    """
    Download file from Supabase Storage.
    
    Args:
        file_url: URL of the file
        bucket: Storage bucket name
        
    Returns:
        BytesIO object or None
    """
    if not file_url:
        return None
    
    try:
        path = urllib.parse.urlparse(file_url).path.split('/')[-1]
        file_bytes = await asyncio.to_thread(
            lambda: supabase.storage.from_(bucket).download(path)
        )
        file_obj = io.BytesIO(file_bytes)
        file_obj.name = path
        return file_obj
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None

async def upload_file_to_storage(file_bytes: bytes, filename: str, bucket: str) -> Optional[str]:
    """
    Upload file to Supabase Storage.
    
    Args:
        file_bytes: File content as bytes
        filename: Name of the file
        bucket: Storage bucket name (cv or pictures)
        
    Returns:
        Public URL of uploaded file or None
    """
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Clean filename - remove special characters
        clean_filename = "".join(c for c in filename if c.isalnum() or c in ('.', '_', '-'))
        unique_filename = f"{timestamp}_{clean_filename}"
        
        logger.info(f"Uploading file to {bucket}/{unique_filename}")
        
        # Determine content type
        content_type = "application/octet-stream"
        if filename.lower().endswith('.pdf'):
            content_type = "application/pdf"
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            content_type = "image/jpeg"
        elif filename.lower().endswith('.png'):
            content_type = "image/png"
        elif filename.lower().endswith('.doc'):
            content_type = "application/msword"
        elif filename.lower().endswith('.docx'):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        # Upload to Supabase Storage
        await asyncio.to_thread(
            lambda: supabase.storage.from_(bucket).upload(
                unique_filename,
                file_bytes,
                {"content-type": content_type}
            )
        )
        
        # Get public URL
        result = supabase.storage.from_(bucket).get_public_url(unique_filename)
        logger.info(f"File uploaded successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error uploading file to storage: {e}", exc_info=True)
        return None


async def delete_file_from_storage(file_url: str, bucket: str) -> bool:
    """
    Delete file from Supabase Storage.
    
    Args:
        file_url: URL of the file to delete
        bucket: Storage bucket name
        
    Returns:
        True if successful
    """
    if not file_url:
        return True
    
    try:
        # Extract filename from URL
        path = urllib.parse.urlparse(file_url).path.split('/')[-1]
        logger.info(f"Deleting file from {bucket}/{path}")
        
        # Delete from storage
        await asyncio.to_thread(
            lambda: supabase.storage.from_(bucket).remove([path])
        )
        
        logger.info(f"File deleted successfully: {path}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting file from storage: {e}", exc_info=True)
        return False


async def log_purchase(
    alias_email: str,
    whatsapp: str,
    plan: str,
    amount: float = None,
    currency: str = "USD",
    payment_method: str = None,
    transaction_id: str = None,
    notes: str = None
) -> bool:
    """
    Log a purchase to purchase_history table.
    
    Args:
        alias_email: Applicant's alias email
        whatsapp: Applicant's WhatsApp number
        plan: Application plan (Casual, Normal, Intense)
        amount: Payment amount
        currency: Currency code
        payment_method: Payment method used
        transaction_id: Transaction ID from payment processor
        notes: Additional notes
        
    Returns:
        True if successful
    """
    try:
        purchase_data = {
            "alias_email": alias_email,
            "whatsapp": whatsapp,
            "plan": plan,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "transaction_id": transaction_id,
            "notes": notes
        }
        
        # Remove None values
        purchase_data = {k: v for k, v in purchase_data.items() if v is not None}
        
        result = await asyncio.to_thread(
            lambda: supabase.table("purchase_history")
            .insert(purchase_data)
            .execute()
        )
        
        logger.info(f"Purchase logged for {alias_email}: {plan}")
        return True
        
    except Exception as e:
        logger.error(f"Error logging purchase: {e}", exc_info=True)
        return False
