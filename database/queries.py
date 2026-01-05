import asyncio
import io
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
