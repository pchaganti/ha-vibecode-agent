"""Calendar & Todo API endpoints"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
import logging
from datetime import datetime, timedelta

from app.services.ha_client import ha_client

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')


@router.get("/list")
async def list_calendars():
    """List all calendar entities."""
    try:
        result = await ha_client._request('GET', '/api/calendars')
        return {
            "success": True,
            "count": len(result) if isinstance(result, list) else 0,
            "calendars": result
        }
    except Exception as e:
        logger.error(f"Failed to list calendars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_calendar_events(
    entity_id: str = Query(..., description="Calendar entity ID (e.g., 'calendar.personal')"),
    start: Optional[str] = Query(None, description="Start time ISO format (default: now)"),
    end: Optional[str] = Query(None, description="End time ISO format (default: 7 days from now)"),
):
    """Get events from a calendar entity."""
    try:
        start_time = start or datetime.utcnow().isoformat()
        end_time = end or (datetime.utcnow() + timedelta(days=7)).isoformat()

        result = await ha_client._request(
            'GET',
            f'/api/calendars/{entity_id}',
            params={"start": start_time, "end": end_time}
        )

        return {
            "success": True,
            "entity_id": entity_id,
            "count": len(result) if isinstance(result, list) else 0,
            "events": result
        }
    except Exception as e:
        logger.error(f"Failed to get calendar events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/todos")
async def list_todos(
    entity_id: str = Query(..., description="Todo list entity ID (e.g., 'todo.shopping_list')"),
):
    """Get items from a todo list entity."""
    try:
        result = await ha_client._request(
            'GET',
            f'/api/states/{entity_id}'
        )

        items = []
        if isinstance(result, dict):
            items = result.get("attributes", {}).get("items", [])

        return {
            "success": True,
            "entity_id": entity_id,
            "count": len(items),
            "items": items
        }
    except Exception as e:
        logger.error(f"Failed to list todos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/todos/create")
async def create_todo(
    entity_id: str = Body(..., description="Todo list entity ID (e.g., 'todo.shopping_list')"),
    item: str = Body(..., description="Todo item text"),
):
    """Add an item to a todo list."""
    try:
        result = await ha_client.call_service(
            "todo", "add_item",
            {"entity_id": entity_id, "item": item}
        )
        logger.info(f"Todo item added to {entity_id}: {item}")
        return {
            "success": True,
            "message": f"Todo item added: {item}",
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to create todo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
