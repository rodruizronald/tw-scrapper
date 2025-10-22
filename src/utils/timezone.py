from datetime import datetime
from zoneinfo import ZoneInfo

# Fixed timezone for Costa Rica
LOCAL_TZ = ZoneInfo("America/Costa_Rica")


def now_local() -> datetime:
    """
    Get current datetime in Costa Rica timezone.

    Returns:
        Current datetime in Costa Rica timezone.
    """
    return datetime.now(LOCAL_TZ)
