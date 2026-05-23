from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.config import settings

def get_now() -> datetime:
    """
    Returns the current datetime in the configured timezone (America/Mexico_City).
    The datetime is returned as a naive object (without tzinfo) to maintain
    compatibility with the existing database schema if necessary, 
    but representing the local time.
    """
    tz = ZoneInfo(settings.TIMEZONE)
    return datetime.now(tz).replace(tzinfo=None)

def get_now_aware() -> datetime:
    """
    Returns the current datetime with timezone information.
    """
    tz = ZoneInfo(settings.TIMEZONE)
    return datetime.now(tz)
