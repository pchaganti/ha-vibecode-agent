"""Helpers API endpoints"""
from fastapi import APIRouter, HTTPException
import logging
import os
import yaml
from typing import Dict, Any

from app.models.schemas import HelperCreate, Response
from app.services.ha_client import ha_client
from app.services.ha_websocket import get_ws_client
from app.services.git_manager import git_manager

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')

HELPERS_FILE = "/config/helpers.yaml"
CONFIG_FILE = "/config/configuration.yaml"


def _load_helpers_yaml() -> Dict[str, Any]:
    """Load helpers.yaml file, create if doesn't exist"""
    if not os.path.exists(HELPERS_FILE):
        # Create empty helpers file with all domains
        empty_helpers = {
            'input_boolean': {},
            'input_text': {},
            'input_number': {},
            'input_datetime': {},
            'input_select': {}
        }
        with open(HELPERS_FILE, 'w') as f:
            yaml.dump(empty_helpers, f, default_flow_style=False, allow_unicode=True)
        logger.info(f"Created new {HELPERS_FILE}")
        return empty_helpers
    
    with open(HELPERS_FILE, 'r') as f:
        content = yaml.safe_load(f) or {}
    return content


def _save_helpers_yaml(data: Dict[str, Any]) -> None:
    """Save helpers.yaml file"""
    with open(HELPERS_FILE, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    logger.info(f"Saved {HELPERS_FILE}")


def _ensure_helpers_in_config() -> None:
    """Ensure helpers.yaml is included in configuration.yaml"""
    if not os.path.exists(CONFIG_FILE):
        logger.warning(f"{CONFIG_FILE} not found")
        return
    
    with open(CONFIG_FILE, 'r') as f:
        config_content = f.read()
    
    # Check if already includes helpers.yaml
    if 'helpers.yaml' in config_content or 'input_boolean: !include' in config_content:
        logger.info("helpers.yaml already referenced in configuration.yaml")
        return
    
    # Add reference at the end
    with open(CONFIG_FILE, 'a') as f:
        f.write('\n\n# Input Helpers\n')
        f.write('input_boolean: !include helpers.yaml\n')
        f.write('input_text: !include helpers.yaml\n')
        f.write('input_number: !include helpers.yaml\n')
        f.write('input_datetime: !include helpers.yaml\n')
        f.write('input_select: !include helpers.yaml\n')
    
    logger.info("Added helpers.yaml reference to configuration.yaml")


def _generate_entity_id(domain: str, name: str, existing_helpers: Dict) -> str:
    """Generate entity_id from name"""
    # Convert name to entity_id format: lowercase, replace spaces with underscores
    base_id = name.lower().replace(' ', '_').replace('-', '_')
    base_id = ''.join(c for c in base_id if c.isalnum() or c == '_')
    
    # Check if exists in current helpers
    domain_helpers = existing_helpers.get(domain, {})
    entity_id = base_id
    counter = 1
    
    while entity_id in domain_helpers:
        entity_id = f"{base_id}_{counter}"
        counter += 1
    
    return entity_id


@router.get("/debug/services")
async def debug_services():
    """Debug endpoint to see available services for helpers"""
    try:
        ws_client = await get_ws_client()
        all_services = await ws_client.get_services()
        
        # Extract helper-related services
        helper_services = {}
        for domain in ['input_boolean', 'input_text', 'input_number', 'input_datetime', 'input_select']:
            if domain in all_services:
                helper_services[domain] = all_services[domain]
        
        return {
            "success": True,
            "helper_services": helper_services
        }
    except Exception as e:
        logger.error(f"Failed to get services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_helpers():
    """
    List all input helpers
    
    Returns all entities from helper domains:
    - input_boolean
    - input_text
    - input_number
    - input_datetime
    - input_select
    
    Example response:
    ```json
    {
      "success": true,
      "count": 15,
      "helpers": [
        {
          "entity_id": "input_boolean.climate_system_enabled",
          "state": "on",
          "attributes": {...}
        }
      ]
    }
    ```
    """
    try:
        # Get all entities
        all_states = await ha_client.get_states()
        
        # Filter helper entities
        helper_domains = ['input_boolean', 'input_text', 'input_number', 'input_datetime', 'input_select']
        helpers = [
            entity for entity in all_states 
            if any(entity['entity_id'].startswith(f"{domain}.") for domain in helper_domains)
        ]
        
        logger.info(f"Listed {len(helpers)} helpers")
        
        return {
            "success": True,
            "count": len(helpers),
            "helpers": helpers
        }
    except Exception as e:
        logger.error(f"Failed to list helpers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create", response_model=Response)
async def create_helper(helper: HelperCreate):
    """
    Create input helper via YAML configuration
    
    **Method:** Writes to helpers.yaml and reloads the integration
    
    **Helper types:**
    - `input_boolean` - Toggle/switch
    - `input_text` - Text input
    - `input_number` - Number slider
    - `input_datetime` - Date/time picker
    - `input_select` - Dropdown selection
    
    **Example request (Boolean):**
    ```json
    {
      "type": "input_boolean",
      "config": {
        "name": "My Switch",
        "icon": "mdi:toggle-switch",
        "initial": false
      }
    }
    ```
    
    **Example request (Number):**
    ```json
    {
      "type": "input_number",
      "config": {
        "name": "My Number",
        "min": 0,
        "max": 100,
        "step": 5,
        "unit_of_measurement": "°C",
        "icon": "mdi:thermometer"
      }
    }
    ```
    """
    try:
        # Validate helper type
        valid_types = ['input_boolean', 'input_text', 'input_number', 'input_datetime', 'input_select']
        if helper.type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid helper type. Must be one of: {', '.join(valid_types)}")
        
        # Extract name from config (required)
        if 'name' not in helper.config:
            raise HTTPException(status_code=400, detail="config must include 'name' field")
        
        helper_name = helper.config['name']
        
        # Load existing helpers
        helpers_data = _load_helpers_yaml()
        
        # Ensure domain exists in data
        if helper.type not in helpers_data:
            helpers_data[helper.type] = {}
        
        # Generate entity_id
        entity_id = _generate_entity_id(helper.type, helper_name, helpers_data)
        
        # Remove 'name' from config as it's used as the key
        config_without_name = {k: v for k, v in helper.config.items() if k != 'name'}
        config_without_name['name'] = helper_name  # Add it back as a value
        
        # Add helper to YAML data
        helpers_data[helper.type][entity_id] = config_without_name
        
        # Save helpers.yaml
        _save_helpers_yaml(helpers_data)
        
        # Ensure helpers.yaml is included in configuration.yaml
        _ensure_helpers_in_config()
        
        # Reload the specific helper domain
        ws_client = await get_ws_client()
        await ws_client.call_service(helper.type, 'reload', {})
        logger.info(f"Reloaded {helper.type} integration")
        
        full_entity_id = f"{helper.type}.{entity_id}"
        
        # Commit changes
        if git_manager.enabled:
            await git_manager.commit_changes(f"Create helper: {full_entity_id} - {helper_name}")
        
        logger.info(f"Created helper: {full_entity_id} - {helper_name}")
        
        return Response(
            success=True,
            message=f"Helper created: {full_entity_id} - {helper_name}",
            data={"entity_id": full_entity_id, "name": helper_name, "config": config_without_name}
        )
    except Exception as e:
        logger.error(f"Failed to create helper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{entity_id}")
async def delete_helper(entity_id: str):
    """
    Delete input helper from YAML configuration
    
    **Method:** Removes from helpers.yaml and reloads the integration
    
    Example:
    - `/api/helpers/delete/input_boolean.my_switch`
    """
    try:
        # Parse entity_id
        if '.' not in entity_id:
            raise HTTPException(status_code=400, detail="Invalid entity_id format. Expected: domain.entity_id")
        
        domain, helper_id = entity_id.split('.', 1)
        
        # Validate domain
        valid_types = ['input_boolean', 'input_text', 'input_number', 'input_datetime', 'input_select']
        if domain not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid helper domain. Must be one of: {', '.join(valid_types)}")
        
        # Load existing helpers
        helpers_data = _load_helpers_yaml()
        
        # Check if helper exists
        if domain not in helpers_data or helper_id not in helpers_data[domain]:
            raise HTTPException(status_code=404, detail=f"Helper {entity_id} not found in helpers.yaml")
        
        # Remove helper
        del helpers_data[domain][helper_id]
        
        # Save helpers.yaml
        _save_helpers_yaml(helpers_data)
        
        # Reload the specific helper domain
        ws_client = await get_ws_client()
        await ws_client.call_service(domain, 'reload', {})
        logger.info(f"Reloaded {domain} integration")
        
        # Commit changes
        if git_manager.enabled:
            await git_manager.commit_changes(f"Delete helper: {entity_id}")
        
        logger.info(f"Deleted helper: {entity_id}")
        
        return Response(
            success=True,
            message=f"Helper deleted: {entity_id}",
            data={"entity_id": entity_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete helper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

