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
async def create_script(script: ScriptData):
    """
    Create new script
    
    **Example:**
    ```json
    {
      "entity_id": "my_script",
      "alias": "My Script",
      "sequence": [
        {"service": "light.turn_on", "target": {"entity_id": "light.living_room"}}
      ],
      "mode": "single",
      "icon": "mdi:play"
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
        
        # Check if exists
        if script.entity_id in scripts:
            raise ValueError(f"Script '{script.entity_id}' already exists")
        
        # Add new script
        scripts[script.entity_id] = script.model_dump(exclude={'entity_id'}, exclude_none=True)
        
        # Write back
        new_content = yaml.dump(scripts, allow_unicode=True, default_flow_style=False, sort_keys=False)
        await file_manager.write_file('scripts.yaml', new_content, create_backup=True)
        
        # Reload
        await ha_client.reload_component('scripts')
        
        # Commit
        if git_manager.enabled:
            await git_manager.commit_changes(f"Create script: {script.alias}")
        
        logger.info(f"Created script: {script.entity_id}")
        
        return Response(success=True, message=f"Script created: {script.entity_id}")
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
            await git_manager.commit_changes(f"Delete script: {script_id}")
        
        logger.info(f"Deleted script: {script_id}")
        
        return Response(success=True, message=f"Script deleted: {script_id}")
    except Exception as e:
        logger.error(f"Failed to delete script: {e}")
        raise HTTPException(status_code=500, detail=str(e))

