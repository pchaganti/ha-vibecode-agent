"""Helpers API endpoints"""
from fastapi import APIRouter, HTTPException
import logging

from app.models.schemas import HelperCreate, Response
from app.services.ha_client import ha_client
from app.services.git_manager import git_manager

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')

@router.post("/create", response_model=Response)
async def create_helper(helper: HelperCreate):
    """
    Create input helper
    
    **Helper types:**
    - `input_boolean` - Toggle/switch
    - `input_text` - Text input
    - `input_number` - Number slider
    - `input_datetime` - Date/time picker
    - `input_select` - Dropdown selection
    
    **Example request (Boolean):**
    ```json
    {
      "domain": "input_boolean",
      "entity_id": "my_switch",
      "name": "My Switch",
      "config": {
        "icon": "mdi:toggle-switch",
        "initial": false
      }
    }
    ```
    
    **Example request (Number):**
    ```json
    {
      "domain": "input_number",
      "entity_id": "my_number",
      "name": "My Number",
      "config": {
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
        # Construct service data
        service_data = {
            "name": helper.name,
            **helper.config
        }
        
        # Create helper via service call
        # Note: This creates the helper in the UI, not in YAML
        result = await ha_client.call_service(
            helper.domain,
            'create',
            service_data
        )
        
        # Commit changes
        if git_manager.enabled:
            await git_manager.commit_changes(f"Create helper: {helper.domain}.{helper.entity_id}")
        
        logger.info(f"Created helper: {helper.domain}.{helper.entity_id}")
        
        return Response(
            success=True,
            message=f"Helper created: {helper.domain}.{helper.entity_id}",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to create helper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{entity_id}")
async def delete_helper(entity_id: str):
    """
    Delete input helper
    
    Example:
    - `/api/helpers/delete/input_boolean.my_switch`
    """
    try:
        # Get domain from entity_id
        domain = entity_id.split('.')[0]
        
        # Delete via service
        await ha_client.call_service(
            domain,
            'delete',
            {"entity_id": entity_id}
        )
        
        logger.info(f"Deleted helper: {entity_id}")
        
        return Response(
            success=True,
            message=f"Helper deleted: {entity_id}"
        )
    except Exception as e:
        logger.error(f"Failed to delete helper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

