"""System API endpoints"""
from fastapi import APIRouter, HTTPException, Query
import logging

from app.models.schemas import Response
from app.services.ha_client import ha_client

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')

@router.post("/reload", response_model=Response)
async def reload_component(
    component: str = Query(..., description="Component to reload: automations, scripts, templates, core, all")
):
    """
    Reload Home Assistant component
    
    **Available components:**
    - `automations` - Reload automations
    - `scripts` - Reload scripts
    - `templates` - Reload template entities
    - `core` - Reload core configuration
    - `all` - Reload all reloadable components
    
    **Example:**
    - `/api/system/reload?component=automations`
    """
    try:
        result = await ha_client.reload_component(component)
        logger.info(f"Reloaded component: {component}")
        
        return Response(
            success=True,
            message=f"Component reloaded: {component}",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to reload component: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-config", response_model=Response)
@router.post("/check_config", response_model=Response)  # Legacy compatibility
async def check_config():
    """
    Check Home Assistant configuration validity
    
    Returns validation results with detailed error messages (like Developer Tools → Check Configuration)
    """
    try:
        result = await ha_client.check_config()
        logger.info("Configuration check completed")
        
        # Check if result contains errors
        if isinstance(result, dict) and 'errors' in result and result['errors']:
            # Configuration has errors
            errors = result['errors']
            error_summary = "\n".join(errors) if isinstance(errors, list) else str(errors)
            
            logger.error(f"Configuration has {len(errors) if isinstance(errors, list) else 'some'} errors")
            
            return Response(
                success=False,
                message=f"Configuration invalid!\n\n{error_summary}",
                data=result
            )
        
        return Response(
            success=True,
            message="Configuration is valid",
            data=result
        )
    except Exception as e:
        logger.error(f"Configuration check failed: {e}")
        
        # Try to extract detailed error from exception
        error_msg = str(e)
        
        # If it's HA API error with response data, try to parse it
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            try:
                import json
                error_data = json.loads(e.response.text)
                if 'message' in error_data:
                    error_msg = error_data['message']
            except Exception:
                pass
        
        return Response(
            success=False,
            message=f"Configuration check failed: {error_msg}",
            data=None
        )

@router.post("/restart", response_model=Response)
async def restart_ha():
    """
    Restart Home Assistant
    
    **⚠️ WARNING: This will restart your Home Assistant instance!**
    """
    try:
        await ha_client.restart()
        logger.warning("Home Assistant restart initiated")
        
        return Response(
            success=True,
            message="Home Assistant restart initiated"
        )
    except Exception as e:
        logger.error(f"Failed to restart HA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_config():
    """Get Home Assistant configuration"""
    try:
        config = await ha_client.get_config()
        return {
            "success": True,
            "config": config
        }
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repairs")
async def get_repairs():
    """
    Get Home Assistant repair issues (configuration problems, deprecations, etc.)

    Returns a list of active repair issues that need attention, similar to
    Settings -> System -> Repairs in the HA UI.
    """
    try:
        result = await ha_client._request('GET', '/api/repairs/issues')
        issues = result.get('issues', result) if isinstance(result, dict) else result
        return {
            "success": True,
            "total": len(issues) if isinstance(issues, list) else 0,
            "issues": issues
        }
    except Exception as e:
        logger.error(f"Failed to get repair issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

