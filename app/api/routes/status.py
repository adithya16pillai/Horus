from fastapi import APIRouter, Depends
import platform
from datetime import datetime, timedelta
import time
import psutil
import os

from app.core.config import get_settings
from app.core.security import get_api_key

router = APIRouter(tags=["Status"])

START_TIME = time.time()


@router.get("/status", summary="Get service status")
async def get_status():
    """
    Get basic service status information.
    This endpoint is public and can be used for health checks.
    """
    settings = get_settings()
    
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "uptime": format_uptime(START_TIME),
    }


@router.get("/status/detailed", summary="Get detailed service status")
async def get_detailed_status(api_key: str = Depends(get_api_key)):
    settings = get_settings()
    
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "service": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "healthy",
            "uptime": format_uptime(START_TIME),
            "start_time": datetime.fromtimestamp(START_TIME).isoformat(),
        },
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "memory": {
                "total": format_bytes(memory.total),
                "available": format_bytes(memory.available),
                "used": format_bytes(memory.used),
                "percent": memory.percent,
            },
            "disk": {
                "total": format_bytes(disk.total),
                "free": format_bytes(disk.free),
                "used": format_bytes(disk.used),
                "percent": disk.percent,
            },
        },
        "configuration": {
            "debug_mode": settings.DEBUG,
            "log_level": settings.LOG_LEVEL,
            "notification_method": settings.NOTIFICATION_METHOD,
        }
    }


def format_uptime(start_time):
    """Format the uptime in a human-readable way"""
    uptime_seconds = time.time() - start_time
    delta = timedelta(seconds=int(uptime_seconds))
    
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)


def format_bytes(bytes_value):
    """Format bytes in a human-readable way"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024 or unit == 'TB':
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024