from datetime import date, datetime
from zoneinfo import ZoneInfo

# Fixed timezone for Costa Rica
LOCAL_TZ = ZoneInfo("America/Costa_Rica")

# Fixed timezone for UTC
UTC_TZ = ZoneInfo("UTC")


def now_utc() -> datetime:
    """Get current datetime in UTC (for MongoDB storage)."""
    return datetime.now(UTC_TZ)


def now_local() -> datetime:
    """Get current datetime in local timezone."""
    return datetime.now(LOCAL_TZ)


def today_local() -> date:
    """Get current date in local timezone."""
    return now_local().date()


def utc_to_local(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to local timezone."""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=UTC_TZ)
    return utc_dt.astimezone(LOCAL_TZ)
