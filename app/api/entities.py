"""Entities API endpoints"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
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

@router.post("/call_service")
async def call_service(
    domain: str = Body(..., description="Service domain (e.g., 'number', 'light', 'climate')"),
    service: str = Body(..., description="Service name (e.g., 'set_value', 'turn_on', 'set_temperature')"),
    service_data: Optional[Dict[str, Any]] = Body(None, description="Service data (e.g., {'entity_id': 'number.alex_trv_local_temperature_offset', 'value': -2.0})"),
    target: Optional[Dict[str, Any]] = Body(None, description="Target entity/entities (e.g., {'entity_id': 'light.living_room'})")
):
    """
    Call a Home Assistant service
    
    Examples:
    - Set number value: {"domain": "number", "service": "set_value", "service_data": {"entity_id": "number.alex_trv_local_temperature_offset", "value": -2.0}}
    - Turn on light: {"domain": "light", "service": "turn_on", "target": {"entity_id": "light.living_room"}}
    - Set climate temperature: {"domain": "climate", "service": "set_temperature", "target": {"entity_id": "climate.bedroom_trv_thermostat"}, "service_data": {"temperature": 21.0}}
    """
    try:
        # Combine service_data and target into data dict
        # In Home Assistant API, target is merged with service_data
        data = {}
        if service_data:
            data.update(service_data)
        if target:
            # Merge target fields into data (e.g., entity_id from target)
            if 'entity_id' in target:
                data['entity_id'] = target['entity_id']
            if 'area_id' in target:
                data['area_id'] = target['area_id']
            if 'device_id' in target:
                data['device_id'] = target['device_id']
            # Also keep target for services that need it
            if not any(k in data for k in ['entity_id', 'area_id', 'device_id']):
                data['target'] = target
        
        result = await ha_client.call_service(domain, service, data)
        logger.info(f"Service called: {domain}.{service}")
        return {
            "success": True,
            "domain": domain,
            "service": service,
            "data": data,
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to call service {domain}.{service}: {e}")
        raise HTTPException(status_code=500, detail=f"Service call failed: {str(e)}")

@router.post("/rename")
async def rename_entity(
    old_entity_id: str = Body(..., description="Current entity_id (e.g., 'climate.sonoff_trvzb_thermostat')"),
    new_entity_id: str = Body(..., description="New entity_id (e.g., 'climate.office_trv_thermostat')"),
    new_name: Optional[str] = Body(None, description="Optional new friendly name")
):
    """
    Rename an entity_id via Entity Registry WebSocket API
    
    This will update the entity_id in Home Assistant's entity registry.
    Note: After renaming, you may need to reload automations/scripts that reference the entity.
    
    Example:
    - {"old_entity_id": "climate.sonoff_trvzb_thermostat", "new_entity_id": "climate.office_trv_thermostat", "new_name": "Office TRV Thermostat"}
    """
    try:
        result = await ha_client.rename_entity(old_entity_id, new_entity_id, new_name)
        logger.info(f"Renamed entity: {old_entity_id} → {new_entity_id}")
        return {
            "success": True,
            "old_entity_id": old_entity_id,
            "new_entity_id": new_entity_id,
            "new_name": new_name,
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to rename entity {old_entity_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rename entity: {str(e)}")

