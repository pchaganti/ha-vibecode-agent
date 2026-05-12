"""Blueprints API endpoints"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
import logging

from app.services.ha_client import ha_client

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')


@router.get("/list")
async def list_blueprints(
    domain: str = Query("automation", description="Blueprint domain: 'automation' or 'script'"),
):
    """List available blueprints."""
    try:
        result = await ha_client._request('GET', f'/api/config/{domain}/config/blueprints')

        blueprints = []
        if isinstance(result, dict):
            for path, bp_data in result.items():
                bp_info = {"path": path}
                if isinstance(bp_data, dict):
                    metadata = bp_data.get("metadata", bp_data)
                    bp_info["name"] = metadata.get("name", path)
                    bp_info["description"] = metadata.get("description", "")
                    bp_info["domain"] = metadata.get("domain", domain)
                    bp_info["source_url"] = metadata.get("source_url", "")
                blueprints.append(bp_info)

        return {
            "success": True,
            "domain": domain,
            "count": len(blueprints),
            "blueprints": blueprints
        }
    except Exception as e:
        logger.error(f"Failed to list blueprints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_blueprint(
    url: str = Body(..., description="URL to import blueprint from (e.g., community forum or GitHub URL)"),
):
    """Import a blueprint from a URL."""
    try:
        result = await ha_client._request('POST', '/api/config/blueprint/import', data={"url": url})
        logger.info(f"Blueprint imported from: {url}")
        return {
            "success": True,
            "message": f"Blueprint imported from {url}",
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to import blueprint from {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
