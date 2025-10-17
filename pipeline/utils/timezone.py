from datetime import datetime
from zoneinfo import ZoneInfo

# Fixed timezone for Costa Rica
COSTA_RICA_TZ = ZoneInfo("America/Costa_Rica")
UTC_TZ = ZoneInfo("UTC")


def now_local() -> datetime:
    """
    Get current datetime in Costa Rica timezone.

    Returns:
        Current datetime in Costa Rica timezone.
    """
    return datetime.now(COSTA_RICA_TZ)


def now_utc() -> datetime:
    """
    Get current datetime in UTC.

    Returns:
        Current datetime in UTC timezone.
    """
    return datetime.now(UTC_TZ)


def to_local(dt: datetime) -> datetime:
    """
    Convert a datetime to Costa Rica timezone.

    Args:
        dt: Datetime to convert (can be naive or timezone-aware).

    Returns:
        Datetime converted to Costa Rica timezone.
    """
    # If datetime is naive, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)

    return dt.astimezone(COSTA_RICA_TZ)


def to_utc(dt: datetime) -> datetime:
    """
    Convert a datetime to UTC.

    Args:
        dt: Datetime to convert (can be naive or timezone-aware).

    Returns:
        Datetime converted to UTC.
    """
    # If datetime is naive, assume it's in Costa Rica timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=COSTA_RICA_TZ)

    return dt.astimezone(UTC_TZ)
