"""Entities API endpoints"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from app.services.ha_client import ha_client

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')

@router.get("/list")
async def list_entities(
    domain: Optional[str] = Query(None, description="Filter by domain (e.g., 'sensor', 'climate')"),
    search: Optional[str] = Query(None, description="Search in entity_id or friendly_name")
):
    """
    Get all entities with their states
    
    Examples:
    - `/api/entities/list` - All entities
    - `/api/entities/list?domain=climate` - Only climate entities
    - `/api/entities/list?search=bedroom` - Search for 'bedroom'
    """
    try:
        states = await ha_client.get_states()
        
        # Filter by domain
        if domain:
            states = [s for s in states if s['entity_id'].startswith(f"{domain}.")]
        
        # Search
        if search:
            search_lower = search.lower()
            states = [
                s for s in states 
                if search_lower in s['entity_id'].lower() or 
                   search_lower in s.get('attributes', {}).get('friendly_name', '').lower()
            ]
        
        logger.info(f"Listed {len(states)} entities")
        return {
            "success": True,
            "count": len(states),
            "entities": states
        }
    except Exception as e:
        logger.error(f"Failed to list entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/state/{entity_id}")
async def get_entity_state(entity_id: str):
    """
    Get specific entity state
    
    Example:
    - `/api/entities/state/climate.bedroom_trv_thermostat`
    """
    try:
        state = await ha_client.get_state(entity_id)
        return {
            "success": True,
            "entity_id": entity_id,
            "state": state
        }
    except Exception as e:
        logger.error(f"Failed to get entity state: {e}")
        raise HTTPException(status_code=404, detail=f"Entity not found: {entity_id}")

@router.get("/services")
async def list_services():
    """
    Get all available Home Assistant services
    
    Returns complete list of services with descriptions
    """
    try:
        services = await ha_client.get_services()
        return {
            "success": True,
            "count": len(services),
            "services": services
        }
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

