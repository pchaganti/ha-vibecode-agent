"""Scripts API endpoints"""
from fastapi import APIRouter, HTTPException
import yaml
import logging

from app.models.schemas import ScriptData, Response
from app.services.file_manager import file_manager
from app.services.ha_client import ha_client
from app.services.git_manager import git_manager

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')

@router.get("/list")
async def list_scripts():
    """List all scripts from scripts.yaml"""
    try:
        content = await file_manager.read_file('scripts.yaml')
        scripts = yaml.safe_load(content) or {}
        
        return {
            "success": True,
            "count": len(scripts),
            "scripts": scripts
        }
    except FileNotFoundError:
        return {"success": True, "count": 0, "scripts": {}}
    except Exception as e:
        logger.error(f"Failed to list scripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create", response_model=Response)
async def create_script(config: dict):
    """
    Create new script
    
    **Example:**
    ```json
    {
      "test_script": {
        "alias": "Test Script",
        "sequence": [
          {"service": "light.turn_on", "target": {"entity_id": "light.living_room"}}
        ],
        "mode": "single",
        "icon": "mdi:play"
      }
    }
    ```
    
    Or as single script:
    ```json
    {
      "entity_id": "my_script",
      "alias": "My Script",
      "sequence": [...],
      "mode": "single"
    }
    ```
    """
    try:
        # Read existing scripts
        try:
            content = await file_manager.read_file('scripts.yaml')
            scripts = yaml.safe_load(content) or {}
        except FileNotFoundError:
            scripts = {}
        
        # Handle two formats:
        # Format 1: {"script_id": {"alias": ..., "sequence": ...}}
        # Format 2: {"entity_id": "...", "alias": ..., "sequence": ...}
        
        if 'entity_id' in config:
            # Format 2: Single script with entity_id field
            entity_id = config.pop('entity_id')
            script_data = config
        else:
            # Format 1: Dictionary with script_id as key
            if len(config) != 1:
                raise ValueError("Config must contain exactly one script")
            entity_id = list(config.keys())[0]
            script_data = config[entity_id]
        
        # Check if exists
        if entity_id in scripts:
            raise ValueError(f"Script '{entity_id}' already exists")
        
        # Add new script
        scripts[entity_id] = script_data
        
        # Write back
        new_content = yaml.dump(scripts, allow_unicode=True, default_flow_style=False, sort_keys=False)
        await file_manager.write_file('scripts.yaml', new_content, create_backup=True)
        
        # Reload
        await ha_client.reload_component('scripts')
        
        # Commit
        if git_manager.enabled:
            script_alias = script_data.get('alias', entity_id)
            await git_manager.commit_changes(
                f"Create script: {script_alias}",
                skip_if_processing=True
            )
        
        logger.info(f"Created script: {entity_id}")
        
        return Response(success=True, message=f"Script created: {entity_id}")
    except Exception as e:
        logger.error(f"Failed to create script: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{script_id}")
async def delete_script(script_id: str):
    """Delete script by ID"""
    try:
        content = await file_manager.read_file('scripts.yaml')
        scripts = yaml.safe_load(content) or {}
        
        if script_id not in scripts:
            raise HTTPException(status_code=404, detail=f"Script not found: {script_id}")
        
        del scripts[script_id]
        
        new_content = yaml.dump(scripts, allow_unicode=True, default_flow_style=False, sort_keys=False)
        await file_manager.write_file('scripts.yaml', new_content, create_backup=True)
        
        await ha_client.reload_component('scripts')
        
        if git_manager.enabled:
            await git_manager.commit_changes(
                f"Delete script: {script_id}",
                skip_if_processing=True
            )
        
        logger.info(f"Deleted script: {script_id}")
        
        return Response(success=True, message=f"Script deleted: {script_id}")
    except Exception as e:
        logger.error(f"Failed to delete script: {e}")
        raise HTTPException(status_code=500, detail=str(e))

