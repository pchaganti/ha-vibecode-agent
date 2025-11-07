"""Logs API endpoints"""
from fastapi import APIRouter, Query
from typing import Optional
import logging

from app.utils.logger import get_logs

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')

@router.get("/")
async def get_agent_logs(
    limit: int = Query(100, description="Number of log entries to return"),
    level: Optional[str] = Query(None, description="Filter by level: DEBUG, INFO, WARNING, ERROR")
):
    """
    Get agent logs
    
    Returns recent log entries from the agent
    
    **Examples:**
    - `/api/logs/` - Last 100 log entries
    - `/api/logs/?limit=50` - Last 50 entries
    - `/api/logs/?level=ERROR` - Only errors
    """
    try:
        logs = get_logs(limit=limit, level=level)
        
        return {
            "success": True,
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return {
            "success": False,
            "count": 0,
            "logs": [],
            "error": str(e)
        }

@router.delete("/clear")
async def clear_logs():
    """
    Clear agent logs
    
    Clears the in-memory log buffer
    """
    try:
        from app.utils.logger import LOG_BUFFER
        LOG_BUFFER.clear()
        
        logger.info("Logs cleared")
        
        return {
            "success": True,
            "message": "Logs cleared"
        }
    except Exception as e:
        logger.error(f"Failed to clear logs: {e}")
        return {
            "success": False,
            "message": str(e)
        }

