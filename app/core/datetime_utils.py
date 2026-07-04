from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def utc_now_plus(**kwargs) -> datetime:
    """Return a timezone-aware UTC datetime offset by the given timedelta kwargs."""
    return utc_now() + timedelta(**kwargs)


def ensure_utc_aware(dt: datetime) -> datetime:
    """
    Normalize a datetime to timezone-aware UTC.
    SQLite may return naive datetimes even for timezone=True columns.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
