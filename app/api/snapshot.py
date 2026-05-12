"""Snapshot API — aggregates HA state into a single filtered JSON package."""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Set
import logging
import asyncio

from app.services.ha_client import ha_client
from app.services.ha_websocket import get_ws_client

router = APIRouter()
logger = logging.getLogger('ha_cursor_agent')

VALID_SECTIONS = {"states", "areas", "devices", "config_entries", "automations"}
DEFAULT_SECTIONS = "states,areas"


@router.get("")
async def get_snapshot(
    include: str = Query(
        DEFAULT_SECTIONS,
        description=(
            "Comma-separated sections to include: "
            "states, areas, devices, config_entries, automations. "
            "Default: states,areas"
        ),
    ),
    domains: Optional[str] = Query(
        None,
        description="Comma-separated domain filter for states (e.g. light,switch,sensor)",
    ),
    area_id: Optional[str] = Query(
        None,
        description="Filter states and devices by area_id",
    ),
    summary_only: bool = Query(
        False,
        description="If true, states return only entity_id + state (saves tokens)",
    ),
):
    """
    Aggregate snapshot of the Home Assistant instance.

    Returns selected sections of HA data in a single response so the AI gets
    full context without multiple round-trips. Each section is optional via
    the ``include`` parameter.
    """
    try:
        requested: Set[str] = {s.strip().lower() for s in include.split(",") if s.strip()}
        unknown = requested - VALID_SECTIONS
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown sections: {', '.join(sorted(unknown))}. "
                       f"Valid: {', '.join(sorted(VALID_SECTIONS))}",
            )

        domain_set: Optional[Set[str]] = (
            {d.strip().lower() for d in domains.split(",") if d.strip()}
            if domains
            else None
        )

        ws_client = None
        needs_ws = requested & {"areas", "devices", "config_entries"}
        need_area_filter = area_id and "states" in requested
        if needs_ws or need_area_filter:
            try:
                ws_client = await get_ws_client()
            except Exception as e:
                logger.warning(f"WebSocket unavailable, registry sections will be empty: {e}")

        tasks: Dict[str, asyncio.Task] = {}

        if "states" in requested:
            tasks["states"] = asyncio.create_task(ha_client.get_states())
        if "areas" in requested and ws_client:
            tasks["areas"] = asyncio.create_task(ws_client.get_area_registry_list())
        if ("devices" in requested or need_area_filter) and ws_client:
            tasks["devices"] = asyncio.create_task(ws_client.get_device_registry_list())
        if "config_entries" in requested and ws_client:
            tasks["config_entries"] = asyncio.create_task(
                ws_client._send_message({"type": "config/config_entries/list"})
            )
        if need_area_filter and ws_client:
            tasks["_entity_registry"] = asyncio.create_task(
                ws_client.get_entity_registry_list()
            )

        results: Dict[str, object] = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                logger.error(f"Snapshot: failed to fetch {key}: {e}")
                results[key] = None

        snapshot: Dict[str, object] = {}

        if "states" in requested:
            states: List[Dict] = results.get("states") or []
            if domain_set:
                states = [
                    s for s in states
                    if s.get("entity_id", "").split(".", 1)[0] in domain_set
                ]
            if area_id and ws_client:
                entity_registry: List[Dict] = results.get("_entity_registry") or []
                area_entity_ids: Set[str] = {
                    e.get("entity_id")
                    for e in entity_registry
                    if e.get("area_id") == area_id
                }
                devices_data: List[Dict] = results.get("devices") or []
                if devices_data:
                    area_device_ids = {
                        d.get("id")
                        for d in devices_data
                        if d.get("area_id") == area_id
                    }
                    device_entity_ids = {
                        e.get("entity_id")
                        for e in entity_registry
                        if e.get("device_id") in area_device_ids
                    }
                    area_entity_ids |= device_entity_ids
                states = [s for s in states if s.get("entity_id") in area_entity_ids]

            if summary_only:
                states = [
                    {"entity_id": s.get("entity_id"), "state": s.get("state")}
                    for s in states
                ]

            snapshot["states"] = {"count": len(states), "entities": states}

        if "areas" in requested:
            areas: List[Dict] = results.get("areas") or []
            snapshot["areas"] = {
                "count": len(areas),
                "areas": [
                    {
                        "area_id": a.get("area_id"),
                        "name": a.get("name"),
                        "aliases": a.get("aliases", []),
                        "floor_id": a.get("floor_id"),
                    }
                    for a in areas
                ],
            }

        if "devices" in requested:
            devices: List[Dict] = results.get("devices") or []
            if area_id:
                devices = [d for d in devices if d.get("area_id") == area_id]
            snapshot["devices"] = {
                "count": len(devices),
                "devices": [
                    {
                        "id": d.get("id"),
                        "name": d.get("name") or d.get("name_by_user"),
                        "manufacturer": d.get("manufacturer"),
                        "model": d.get("model"),
                        "area_id": d.get("area_id"),
                        "disabled_by": d.get("disabled_by"),
                    }
                    for d in devices
                ],
            }

        if "config_entries" in requested:
            entries = results.get("config_entries") or []
            if isinstance(entries, list):
                snapshot["config_entries"] = {
                    "count": len(entries),
                    "entries": [
                        {
                            "entry_id": e.get("entry_id"),
                            "domain": e.get("domain"),
                            "title": e.get("title"),
                            "state": e.get("state"),
                        }
                        for e in entries
                    ],
                }
            else:
                snapshot["config_entries"] = {"count": 0, "entries": []}

        if "automations" in requested:
            all_states = results.get("states")
            if all_states is None:
                try:
                    all_states = await ha_client.get_states()
                except Exception:
                    all_states = []
            automations = [
                {
                    "entity_id": s.get("entity_id"),
                    "state": s.get("state"),
                    "alias": s.get("attributes", {}).get("friendly_name"),
                    "last_triggered": s.get("attributes", {}).get("last_triggered"),
                }
                for s in all_states
                if s.get("entity_id", "").startswith("automation.")
            ]
            snapshot["automations"] = {
                "count": len(automations),
                "automations": automations,
            }

        total_entities = snapshot.get("states", {}).get("count", 0)
        logger.info(
            f"Snapshot: sections={list(snapshot.keys())}, "
            f"entities={total_entities}, "
            f"domains={domains or 'all'}, "
            f"area_id={area_id or 'all'}, "
            f"summary_only={summary_only}"
        )

        return {
            "success": True,
            "sections": list(snapshot.keys()),
            **snapshot,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get snapshot: {str(e)}")
