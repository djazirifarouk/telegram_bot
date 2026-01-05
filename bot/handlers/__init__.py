from .start import register_start_handlers
from .view import register_view_handlers
from .edit import register_edit_handlers
from .payment import register_payment_handlers
from .subscription import register_subscription_handlers
from .archive import register_archive_handlers
from .stats import register_stats_handlers
from .file_handler import register_file_handlers
from .skills_handler import register_skills_handlers

__all__ = [
    'register_start_handlers',
    'register_view_handlers',
    'register_edit_handlers',
    'register_payment_handlers',
    'register_subscription_handlers',
    'register_archive_handlers',
    'register_stats_handlers',
    'register_file_handlers',
    'register_skills_handlers',
    'register_all_handlers'
]


def register_all_handlers(application):
    """Register all bot handlers."""
    register_start_handlers(application)
    register_view_handlers(application)
    register_edit_handlers(application)
    register_payment_handlers(application)
    register_subscription_handlers(application)
    register_archive_handlers(application)
    register_stats_handlers(application)
    register_file_handlers(application)
    register_skills_handlers(application)
