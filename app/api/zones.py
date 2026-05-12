"""Zone Management API endpoints"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
import logging

from app.services.ha_client import ha_client

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')


@router.get("/list")
async def list_zones():
    """List all zones configured in Home Assistant."""
    try:
        states = await ha_client.get_states()
        zones = [
            {
                "entity_id": s["entity_id"],
                "name": s.get("attributes", {}).get("friendly_name", ""),
                "latitude": s.get("attributes", {}).get("latitude"),
                "longitude": s.get("attributes", {}).get("longitude"),
                "radius": s.get("attributes", {}).get("radius"),
                "icon": s.get("attributes", {}).get("icon", ""),
            }
            for s in states
            if s["entity_id"].startswith("zone.")
        ]
        return {
            "success": True,
            "count": len(zones),
            "zones": zones
        }
    except Exception as e:
        logger.error(f"Failed to list zones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_zone(
    name: str = Body(..., description="Zone name (e.g., 'Office')"),
    latitude: float = Body(..., description="Zone center latitude"),
    longitude: float = Body(..., description="Zone center longitude"),
    radius: float = Body(100.0, description="Zone radius in meters (default: 100)"),
    icon: Optional[str] = Body(None, description="MDI icon (e.g., 'mdi:office-building')"),
):
    """Create a new zone."""
    try:
        from app.services.ha_websocket import get_ws_client
        ws_client = await get_ws_client()

        zone_data = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
        }
        if icon:
            zone_data["icon"] = icon

        result = await ws_client.send_command("config/zone/create", **zone_data)
        logger.info(f"Zone created: {name}")
        return {
            "success": True,
            "message": f"Zone created: {name}",
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to create zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_zone(
    zone_id: str = Query(..., description="Zone ID to delete (e.g., from zone entity_id without 'zone.' prefix)"),
):
    """Delete a zone."""
    try:
        from app.services.ha_websocket import get_ws_client
        ws_client = await get_ws_client()

        result = await ws_client.send_command("config/zone/delete", zone_id=zone_id)
        logger.info(f"Zone deleted: {zone_id}")
        return {
            "success": True,
            "message": f"Zone deleted: {zone_id}",
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to delete zone: {e}")
        raise HTTPException(status_code=500, detail=str(e))
