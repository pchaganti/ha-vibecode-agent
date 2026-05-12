"""History & Statistics API endpoints"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from datetime import datetime, timedelta, timezone

from app.services.ha_client import ha_client
from app.services.ha_websocket import get_ws_client

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')


@router.get("/list")
async def get_history(
    entity_id: str = Query(..., description="Entity ID to get history for (e.g., 'sensor.temperature')"),
    start: Optional[str] = Query(None, description="Start time ISO format (default: 24h ago). Example: '2026-05-01T00:00:00'"),
    end: Optional[str] = Query(None, description="End time ISO format (default: now). Example: '2026-05-02T00:00:00'"),
    minimal_response: bool = Query(True, description="If true, return minimal state data (less tokens)"),
):
    """Get state history for an entity over a time period."""
    try:
        params = {"filter_entity_id": entity_id}
        if minimal_response:
            params["minimal_response"] = ""
        if end:
            params["end_time"] = end

        start_time = start or (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

        result = await ha_client._request('GET', f'history/period/{start_time}', params=params)

        history = result[0] if isinstance(result, list) and len(result) > 0 else []

        return {
            "success": True,
            "entity_id": entity_id,
            "count": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Failed to get history for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    entity_id: str = Query(..., description="Entity ID to get statistics for"),
    period: str = Query("hour", description="Statistics period: '5minute', 'hour', 'day', 'week', 'month'"),
    start: Optional[str] = Query(None, description="Start time ISO format (default: 7 days ago)"),
    end: Optional[str] = Query(None, description="End time ISO format (default: now)"),
):
    """Get long-term statistics for an entity (energy, temperature trends, etc.)."""
    try:
        start_time = start or (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        end_time = end or datetime.now(timezone.utc).isoformat()

        ws_client = await get_ws_client()
        result = await ws_client._send_message({
            "type": "recorder/statistics_during_period",
            "start_time": start_time,
            "end_time": end_time,
            "statistic_ids": [entity_id],
            "period": period,
        })

        statistics = result.get(entity_id, []) if isinstance(result, dict) else result

        return {
            "success": True,
            "entity_id": entity_id,
            "period": period,
            "count": len(statistics) if isinstance(statistics, list) else 0,
            "statistics": statistics
        }
    except Exception as e:
        logger.error(f"Failed to get statistics for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
