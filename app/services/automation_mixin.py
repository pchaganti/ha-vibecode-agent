"""Automation CRUD operations mixin for HomeAssistantClient"""
import logging
from typing import Dict, List

logger = logging.getLogger('ha_cursor_agent')


class AutomationMixin:
    """Mixin providing automation CRUD methods. Requires _request() from base class."""

    async def list_automations(self, ids_only: bool = False) -> List[Dict]:
        """
        List all automations from Home Assistant (via Entity Registry + file system)
        
        Returns all automations that HA has loaded, regardless of source:
        - From automations.yaml
        - From packages/*.yaml
        - Created via UI (stored in .storage)
        
        Note: Home Assistant doesn't provide WebSocket API for listing automations.
        We use Entity Registry to get all automation entities, then collect their
        configurations from files and .storage.
        
        Args:
            ids_only: If True, return only automation IDs (as strings) for fast listing.
                      If False (default), return full automation configurations.
        
        Returns:
            List of automation configurations (ids_only=False) or list of IDs (ids_only=True)
        """
        def _add_enabled_to_config(config: dict, enabled: bool) -> dict:
            """Return a copy of config with 'enabled' set (avoid mutating cache)."""
            if not isinstance(config, dict):
                return config
            return {**config, 'enabled': enabled}

        try:
            # Import here to avoid circular dependency
            from app.services.ha_websocket import get_ws_client
            from app.services.file_manager import file_manager
            import json
            import yaml
            from pathlib import Path

            # Get all automation entities from Entity Registry
            ws_client = await get_ws_client()
            entity_registry = await ws_client.get_entity_registry_list()
            
            # Filter automation entities
            automation_entities = [
                e for e in entity_registry 
                if e.get('entity_id', '').startswith('automation.')
            ]
            
            automations: List[Dict] = []
            automation_ids_result: List[str] = []
            automation_ids_seen = set()
            
            # OPTIMIZATION: Read all files ONCE and create a cache
            # This prevents reading automations.yaml multiple times (once per automation from Entity Registry)
            automation_cache = {}  # automation_id -> config dict
            
            # Read automations.yaml ONCE
            try:
                content = await file_manager.read_file('automations.yaml', suppress_not_found_logging=True)
                file_automations = yaml.safe_load(content) or []
                if isinstance(file_automations, list):
                    for auto in file_automations:
                        auto_id = auto.get('id')
                        if auto_id:
                            automation_cache[auto_id] = auto
            except Exception:
                pass
            
            # Read packages/*.yaml files ONCE
            try:
                packages_dir = file_manager.config_path / 'packages'
                if packages_dir.exists():
                    for yaml_file in packages_dir.rglob('*.yaml'):
                        try:
                            content = yaml_file.read_text(encoding='utf-8')
                            data = yaml.safe_load(content)
                            if isinstance(data, dict) and 'automation' in data:
                                pkg_automations = data['automation']
                                if isinstance(pkg_automations, list):
                                    for auto in pkg_automations:
                                        auto_id = auto.get('id')
                                        if auto_id:
                                            automation_cache[auto_id] = auto
                                elif isinstance(pkg_automations, dict):
                                    # Handle dict format: {id: config}
                                    for auto_id, auto_config in pkg_automations.items():
                                        auto = dict(auto_config) if isinstance(auto_config, dict) else auto_config
                                        if isinstance(auto, dict):
                                            auto['id'] = auto_id
                                        automation_cache[auto_id] = auto
                        except Exception:
                            continue
            except Exception:
                pass

            # Read automations/*.yaml files ONCE (for !include_dir_merge_list automations/)
            try:
                automations_dir = file_manager.config_path / 'automations'
                if automations_dir.exists() and automations_dir.is_dir():
                    for yaml_file in automations_dir.rglob('*.yaml'):
                        try:
                            content = yaml_file.read_text(encoding='utf-8')
                            data = yaml.safe_load(content)
                            if isinstance(data, list):
                                for auto in data:
                                    if isinstance(auto, dict):
                                        auto_id = auto.get('id')
                                        if auto_id and auto_id not in automation_cache:
                                            automation_cache[auto_id] = auto
                        except Exception:
                            continue
            except Exception:
                pass

            # Read .storage (UI-created automations) ONCE
            try:
                storage_file = file_manager.config_path / '.storage' / 'automation.storage'
                if storage_file.exists():
                    content = storage_file.read_text(encoding='utf-8')
                    storage_data = json.loads(content)
                    if 'data' in storage_data and 'automations' in storage_data['data']:
                        for auto in storage_data['data']['automations']:
                            auto_id = auto.get('id')
                            if auto_id:
                                automation_cache[auto_id] = auto
                            
                            # Also index by entity_id if different from id
                            # This handles cases where Entity Registry uses entity_id that differs from automation id
                            entity_id = auto.get('entity_id', '')
                            if entity_id:
                                if entity_id.startswith('automation.'):
                                    entity_id_clean = entity_id.replace('automation.', '', 1)
                                else:
                                    entity_id_clean = entity_id
                                
                                # Store under entity_id for lookup if different from id
                                if entity_id_clean and entity_id_clean != auto_id:
                                    if entity_id_clean not in automation_cache:
                                        automation_cache[entity_id_clean] = auto
                                
                                # Also store under full entity_id format
                                if entity_id not in automation_cache and entity_id != auto_id:
                                    automation_cache[entity_id] = auto
            except Exception:
                pass
            
            # Now process Entity Registry automations using the cache
            # First, try to match Entity Registry entities with cached automations by entity_id / alias
            # This handles cases where Entity Registry uses different entity_id than automation id
            entity_id_to_auto_map = {}
            for auto in automation_cache.values():
                if isinstance(auto, dict):
                    auto_entity_id = auto.get('entity_id', '')
                    if auto_entity_id:
                        entity_id_to_auto_map[auto_entity_id] = auto
                        if auto_entity_id.startswith('automation.'):
                            entity_id_to_auto_map[auto_entity_id.replace('automation.', '', 1)] = auto
                    # Also index by alias for matching
                    auto_alias = auto.get('alias', '')
                    if auto_alias:
                        # Normalize alias for matching
                        alias_key = auto_alias.lower().replace(' ', '_').replace('-', '_')
                        if alias_key not in entity_id_to_auto_map:
                            entity_id_to_auto_map[alias_key] = auto
            
            # Main pass: iterate over Entity Registry automations
            for entity in automation_entities:
                entity_id = entity.get('entity_id', '')
                if not entity_id.startswith('automation.'):
                    continue
                
                # Extract automation_id from entity_id (automation.xxx -> xxx)
                automation_id = entity_id.replace('automation.', '', 1)
                
                # Also check capabilities.id (for UI-created automations)
                capabilities = entity.get('capabilities', {})
                if isinstance(capabilities, dict):
                    alt_id = capabilities.get('id')
                    if alt_id and alt_id != automation_id:
                        automation_id = alt_id
                
                if automation_id in automation_ids_seen:
                    continue
                automation_ids_seen.add(automation_id)
                
                # Fast path: if only IDs are requested, don't resolve full configs
                if ids_only:
                    if automation_id:
                        automation_ids_result.append(automation_id)
                    continue
                
                # Entity registry enabled state: disabled_by is None => enabled
                enabled = entity.get('disabled_by') is None

                # Try to get config from cache by automation_id
                config = automation_cache.get(automation_id)
                if config:
                    automations.append(_add_enabled_to_config(config, enabled))
                    continue

                # Try to get by entity_id from Entity Registry
                config = entity_id_to_auto_map.get(entity_id)
                if config:
                    automations.append(_add_enabled_to_config(config, enabled))
                    continue

                # Try by automation_id key in map (may be entity_id without prefix or alias key)
                config = entity_id_to_auto_map.get(automation_id)
                if config:
                    automations.append(_add_enabled_to_config(config, enabled))
                    continue

                # Try to match by alias from Entity Registry name
                entity_name = entity.get('name', '')
                if entity_name:
                    alias_key = entity_name.lower().replace(' ', '_').replace('-', '_')
                    config = entity_id_to_auto_map.get(alias_key)
                    if config:
                        automations.append(_add_enabled_to_config(config, enabled))
                        continue

                # Also try matching automation_id normalized as alias
                automation_id_normalized = automation_id.lower().replace(' ', '_').replace('-', '_')
                config = entity_id_to_auto_map.get(automation_id_normalized)
                if config:
                    automations.append(_add_enabled_to_config(config, enabled))
                    continue

                # If still not resolved, include minimal stub with ID
                automations.append({'id': automation_id, 'enabled': enabled})

            # Add file-based automations not in Entity Registry (deduplicate by canonical id)
            for auto_id, auto_config in automation_cache.items():
                canonical_id = (auto_config.get('id') if isinstance(auto_config, dict) else None) or auto_id
                if canonical_id in automation_ids_seen:
                    continue
                automation_ids_seen.add(canonical_id)
                if ids_only:
                    automation_ids_result.append(canonical_id)
                else:
                    # Cache-only automations: enabled unknown, omit or True
                    automations.append(_add_enabled_to_config(auto_config, True))

            if ids_only:
                return list(dict.fromkeys(automation_ids_result))  # deduplicate preserving order
            # Final deduplication by id (keep first occurrence)
            seen_ids: set = set()
            deduped: List[Dict] = []
            for a in automations:
                aid = (a.get('id') if isinstance(a, dict) else None) or ''
                if aid and aid in seen_ids:
                    continue
                if aid:
                    seen_ids.add(aid)
                deduped.append(a)
            return deduped
            
        except Exception as e:
            logger.error(f"Failed to list automations: {e}")
            raise
    
    async def get_automation(self, automation_id: str, _depth: int = 0) -> Dict:
        """
        Get single automation configuration by ID (via files + .storage)
        
        Args:
            automation_id: Automation ID
            _depth: Internal recursion depth guard
            
        Returns:
            Automation configuration dict
        """
        try:
            from app.services.file_manager import file_manager
            import yaml
            import json
            from pathlib import Path
            
            # Try to find in automations.yaml
            try:
                content = await file_manager.read_file('automations.yaml', suppress_not_found_logging=True)
                automations = yaml.safe_load(content) or []
                if isinstance(automations, list):
                    for auto in automations:
                        if auto.get('id') == automation_id:
                            return auto
            except Exception:
                pass
            
            # Try to find in packages/*.yaml
            try:
                packages_dir = file_manager.config_path / 'packages'
                if packages_dir.exists():
                    for yaml_file in packages_dir.rglob('*.yaml'):
                        try:
                            content = yaml_file.read_text(encoding='utf-8')
                            data = yaml.safe_load(content)
                            if isinstance(data, dict) and 'automation' in data:
                                pkg_automations = data['automation']
                                if isinstance(pkg_automations, list):
                                    for auto in pkg_automations:
                                        if auto.get('id') == automation_id:
                                            return auto
                                elif isinstance(pkg_automations, dict):
                                    if automation_id in pkg_automations:
                                        auto = dict(pkg_automations[automation_id]) if isinstance(pkg_automations[automation_id], dict) else pkg_automations[automation_id]
                                        if isinstance(auto, dict):
                                            auto['id'] = automation_id
                                        return auto
                        except Exception:
                            continue
            except Exception:
                pass

            # Try to find in automations/*.yaml (for !include_dir_merge_list automations/)
            try:
                automations_dir = file_manager.config_path / 'automations'
                if automations_dir.exists() and automations_dir.is_dir():
                    for yaml_file in automations_dir.rglob('*.yaml'):
                        try:
                            content = yaml_file.read_text(encoding='utf-8')
                            data = yaml.safe_load(content)
                            if isinstance(data, list):
                                for auto in data:
                                    if isinstance(auto, dict) and auto.get('id') == automation_id:
                                        return auto
                        except Exception:
                            continue
            except Exception:
                pass

            # Try to find in .storage (UI-created automations)
            try:
                storage_file = file_manager.config_path / '.storage' / 'automation.storage'
                if storage_file.exists():
                    content = storage_file.read_text(encoding='utf-8')
                    storage_data = json.loads(content)
                    if 'data' in storage_data and 'automations' in storage_data['data']:
                        for auto in storage_data['data']['automations']:
                            # Check both 'id' field and entity_id from entity registry
                            auto_id = auto.get('id')
                            # Also check if automation_id matches entity_id (without 'automation.' prefix)
                            entity_id = auto.get('entity_id', '')
                            if entity_id.startswith('automation.'):
                                entity_id_clean = entity_id.replace('automation.', '', 1)
                            else:
                                entity_id_clean = entity_id
                            
                            if auto_id == automation_id or entity_id_clean == automation_id:
                                return auto
            except Exception:
                pass
            
            # Fallback: resolve slug via Entity Registry
            # list_automations returns entity_id slugs (e.g. "toilet_cat_alert")
            # but YAML entries use numeric IDs (e.g. "1668201968179")
            if _depth < 2:
                try:
                    from app.services.ha_websocket import get_ws_client
                    ws_client = await get_ws_client()
                    entity_registry = await ws_client.get_entity_registry_list()

                    # Find entity matching this slug
                    target_entity_id = f"automation.{automation_id}" if not automation_id.startswith("automation.") else automation_id
                    for entity in entity_registry:
                        if entity.get('entity_id') == target_entity_id:
                            # Try capabilities.id (the actual config id)
                            caps = entity.get('capabilities', {})
                            real_id = caps.get('id') if isinstance(caps, dict) else None
                            if real_id and real_id != automation_id:
                                return await self.get_automation(real_id, _depth=_depth + 1)
                            # Try unique_id
                            unique_id = entity.get('unique_id')
                            if unique_id and unique_id != automation_id:
                                return await self.get_automation(unique_id, _depth=_depth + 1)
                            break
                except Exception:
                    pass

            raise Exception(f"Automation not found: {automation_id}")

        except Exception as e:
            error_msg = str(e)
            if 'not found' in error_msg.lower():
                raise Exception(f"Automation not found: {automation_id}")
            logger.error(f"Failed to get automation {automation_id}: {e}")
            raise
    
    async def create_automation(self, automation_config: Dict) -> Dict:
        """
        Create new automation via Home Assistant REST API
        
        Uses POST /api/config/automation/config/{automation_id} endpoint.
        Home Assistant automatically determines where to store the automation
        (automations.yaml, packages/*, or .storage).

        Args:
            automation_config: Automation configuration dict (must include 'id')

        Returns:
            Created automation configuration
        """
        automation_id = automation_config.get('id')
        if not automation_id:
            raise ValueError("Automation config must include 'id' field")

        try:
            # Strip prefix if caller passed entity_id format
            if automation_id.startswith("automation."):
                automation_id = automation_id.removeprefix("automation.")

            # Use REST API endpoint: POST /api/config/automation/config/{automation_id}
            endpoint = f"config/automation/config/{automation_id}"
            
            result = await self._request('POST', endpoint, data=automation_config)
            
            logger.info(f"Created automation via REST API: {automation_id}")
            return result
        except Exception as e:
            error_msg = str(e)
            if '409' in error_msg or 'already exists' in error_msg.lower():
                raise ValueError(f"Automation with ID '{automation_id}' already exists")
            logger.error(f"Failed to create automation {automation_id} via REST API: {e}")
            raise
    
    async def update_automation(self, automation_id: str, automation_config: Dict) -> Dict:
        """
        Update existing automation via Home Assistant REST API

        Uses POST /api/config/automation/config/{automation_id} endpoint.
        Home Assistant automatically updates the automation in its original location.

        Args:
            automation_id: Automation ID (plain ID like "office_desk_off")
            automation_config: Updated automation configuration

        Returns:
            Updated automation configuration
        """
        try:
            # Strip prefix if caller passed entity_id format
            if automation_id.startswith("automation."):
                automation_id = automation_id.removeprefix("automation.")

            # Resolve slug to real config ID if needed
            # (e.g. "toilet_cat_alert" -> "1668201968179")
            resolved_id = await self._resolve_automation_id(automation_id)

            # Ensure 'id' matches
            config = dict(automation_config)
            config['id'] = resolved_id

            # Use REST API endpoint: POST /api/config/automation/config/{automation_id}
            endpoint = f"config/automation/config/{resolved_id}"

            result = await self._request('POST', endpoint, data=config)

            logger.info(f"Updated automation via REST API: {resolved_id}")
            return result
        except Exception as e:
            error_msg = str(e)
            if '404' in error_msg or 'not found' in error_msg.lower():
                raise Exception(f"Automation '{automation_id}' not found")
            logger.error(f"Failed to update automation {automation_id} via REST API: {e}")
            raise
    
    async def _resolve_automation_id(self, automation_id: str) -> str:
        """
        Resolve an entity slug to the actual config ID if they differ.

        list_automations returns entity_id slugs (e.g. "toilet_cat_alert") but
        the YAML config uses numeric IDs (e.g. "1668201968179"). The HA REST API
        needs the config ID, not the slug.

        Returns the resolved config ID, or the original automation_id if no
        resolution is needed or possible.
        """
        # Quick check: if get_automation finds it, use the actual config ID from the result
        try:
            auto = await self.get_automation(automation_id)
            config_id = auto.get('id', automation_id)
            if config_id != automation_id:
                logger.info(f"Resolved automation slug '{automation_id}' -> config id '{config_id}'")
            return config_id
        except Exception:
            pass

        # Fallback: resolve via Entity Registry
        try:
            from app.services.ha_websocket import get_ws_client
            ws_client = await get_ws_client()
            entity_registry = await ws_client.get_entity_registry_list()

            target_entity_id = f"automation.{automation_id}"
            for entity in entity_registry:
                if entity.get('entity_id') == target_entity_id:
                    caps = entity.get('capabilities', {})
                    real_id = caps.get('id') if isinstance(caps, dict) else None
                    if real_id and real_id != automation_id:
                        logger.info(f"Resolved automation slug '{automation_id}' -> config id '{real_id}'")
                        return real_id
                    unique_id = entity.get('unique_id')
                    if unique_id and unique_id != automation_id:
                        logger.info(f"Resolved automation slug '{automation_id}' -> unique_id '{unique_id}'")
                        return unique_id
                    break
        except Exception:
            pass

        return automation_id

    async def _find_automation_location(self, automation_id: str) -> Dict:
        """
        Find where an automation is stored (automations.yaml, packages/*.yaml, or .storage)
        
        Checks both 'id' field and 'entity_id' (with and without 'automation.' prefix)
        to handle cases where Entity Registry entity_id differs from automation id.
        
        Returns:
            Dict with keys: 'location' ('automations.yaml', 'packages', or 'storage'),
                           'file_path' (relative path), 'index' (if applicable),
                           'entity_id' (actual entity_id from storage if found)
        """
        from app.services.file_manager import file_manager
        import yaml
        import json
        from pathlib import Path
        
        # Helper to check if automation matches
        def matches_automation(auto, target_id):
            auto_id = auto.get('id')
            if auto_id == target_id:
                return True
            # Also check entity_id (with and without 'automation.' prefix)
            entity_id = auto.get('entity_id', '')
            if entity_id:
                if entity_id.startswith('automation.'):
                    entity_id_clean = entity_id.replace('automation.', '', 1)
                else:
                    entity_id_clean = entity_id
                if entity_id_clean == target_id or entity_id == target_id:
                    return True
            return False
        
        # Try automations.yaml
        try:
            content = await file_manager.read_file('automations.yaml', suppress_not_found_logging=True)
            automations = yaml.safe_load(content) or []
            if isinstance(automations, list):
                for i, auto in enumerate(automations):
                    if matches_automation(auto, automation_id):
                        result = {'location': 'automations.yaml', 'file_path': 'automations.yaml', 'index': i}
                        if auto.get('entity_id'):
                            result['entity_id'] = auto.get('entity_id')
                        return result
        except Exception:
            pass
        
        # Try packages/*.yaml
        try:
            packages_dir = file_manager.config_path / 'packages'
            if packages_dir.exists():
                for yaml_file in packages_dir.rglob('*.yaml'):
                    try:
                        content = yaml_file.read_text(encoding='utf-8')
                        data = yaml.safe_load(content)
                        if isinstance(data, dict) and 'automation' in data:
                            pkg_automations = data['automation']
                            rel_path = yaml_file.relative_to(file_manager.config_path)
                            
                            if isinstance(pkg_automations, list):
                                for i, auto in enumerate(pkg_automations):
                                    if matches_automation(auto, automation_id):
                                        result = {'location': 'packages', 'file_path': str(rel_path), 'index': i, 'format': 'list'}
                                        if auto.get('entity_id'):
                                            result['entity_id'] = auto.get('entity_id')
                                        return result
                            elif isinstance(pkg_automations, dict):
                                if automation_id in pkg_automations:
                                    auto = pkg_automations[automation_id]
                                    result = {'location': 'packages', 'file_path': str(rel_path), 'key': automation_id, 'format': 'dict'}
                                    if isinstance(auto, dict) and auto.get('entity_id'):
                                        result['entity_id'] = auto.get('entity_id')
                                    return result
                                # Also check by entity_id in dict format
                                for key, auto in pkg_automations.items():
                                    if isinstance(auto, dict) and matches_automation(auto, automation_id):
                                        result = {'location': 'packages', 'file_path': str(rel_path), 'key': key, 'format': 'dict'}
                                        if auto.get('entity_id'):
                                            result['entity_id'] = auto.get('entity_id')
                                        return result
                    except Exception:
                        continue
        except Exception:
            pass

        # Try automations/*.yaml (for !include_dir_merge_list automations/)
        try:
            automations_dir = file_manager.config_path / 'automations'
            if automations_dir.exists() and automations_dir.is_dir():
                for yaml_file in automations_dir.rglob('*.yaml'):
                    try:
                        content = yaml_file.read_text(encoding='utf-8')
                        data = yaml.safe_load(content)
                        if isinstance(data, list):
                            for i, auto in enumerate(data):
                                if isinstance(auto, dict) and matches_automation(auto, automation_id):
                                    rel_path = yaml_file.relative_to(file_manager.config_path)
                                    result = {'location': 'automations_dir', 'file_path': str(rel_path), 'index': i, 'format': 'list'}
                                    if auto.get('entity_id'):
                                        result['entity_id'] = auto.get('entity_id')
                                    return result
                    except Exception:
                        continue
        except Exception:
            pass

        # Try .storage (UI-created)
        try:
            storage_file = file_manager.config_path / '.storage' / 'automation.storage'
            if storage_file.exists():
                content = storage_file.read_text(encoding='utf-8')
                storage_data = json.loads(content)
                if 'data' in storage_data and 'automations' in storage_data['data']:
                    for i, auto in enumerate(storage_data['data']['automations']):
                        if matches_automation(auto, automation_id):
                            result = {'location': 'storage', 'file_path': '.storage/automation.storage', 'index': i}
                            if auto.get('entity_id'):
                                result['entity_id'] = auto.get('entity_id')
                            return result
        except Exception:
            pass
        
        return None
    
    async def delete_automation(self, automation_id: str) -> Dict:
        """
        Delete automation from its original location (file-based approach)
        
        Note: Home Assistant REST API does not support DELETE method for automations.
        We find where the automation is stored and remove it from there, then remove
        from Entity Registry and reload automations.
        
        Args:
            automation_id: Automation ID to delete
            
        Returns:
            Deletion result
        """
        try:
            from app.services.file_manager import file_manager
            import yaml
            import json
            
            # Find where automation is located
            location = await self._find_automation_location(automation_id)
            if not location:
                # If automation not found in storage, it might be a "ghost" entry in Entity Registry
                # Try to find by alias and remove all matching entries from Entity Registry
                try:
                    from app.services.ha_websocket import get_ws_client
                    ws_client = await get_ws_client()
                    
                    # Get Entity Registry to find automations by alias
                    entity_registry = await ws_client.get_entity_registry_list()
                    automation_entities = [e for e in entity_registry if e.get('entity_id', '').startswith('automation.')]
                    
                    # Normalize automation_id for alias matching
                    automation_id_normalized = automation_id.lower().replace(' ', '_').replace('-', '_')
                    
                    removed_entities = []
                    for entity in automation_entities:
                        entity_id = entity.get('entity_id', '')
                        entity_name = entity.get('name', '')
                        
                        # Check if entity_id matches
                        if entity_id == f"automation.{automation_id}" or entity_id.replace('automation.', '', 1) == automation_id:
                            try:
                                await ws_client.remove_entity_registry_entry(entity_id)
                                removed_entities.append(entity_id)
                                logger.info(f"Removed ghost automation from Entity Registry by id: {entity_id}")
                            except Exception as e:
                                logger.warning(f"Failed to remove {entity_id}: {e}")
                        
                        # Check if alias/name matches (exact match only to avoid false positives)
                        elif entity_name:
                            entity_name_normalized = entity_name.lower().replace(' ', '_').replace('-', '_')
                            if entity_name_normalized == automation_id_normalized:
                                try:
                                    await ws_client.remove_entity_registry_entry(entity_id)
                                    removed_entities.append(entity_id)
                                    logger.info(f"Removed ghost automation from Entity Registry by alias: {entity_id} (name: {entity_name})")
                                except Exception as e:
                                    logger.warning(f"Failed to remove {entity_id}: {e}")
                    
                    if removed_entities:
                        # Reload automations to sync Entity Registry
                        try:
                            await ws_client.call_service('automation', 'reload')
                            logger.info(f"Reloaded automations after removing ghost entries")
                        except Exception as reload_error:
                            logger.warning(f"Failed to reload automations: {reload_error}")
                        
                        return {'success': True, 'automation_id': automation_id, 'removed_entities': removed_entities, 'message': f'Removed {len(removed_entities)} ghost automation(s) from Entity Registry'}
                    else:
                        raise Exception(f"Automation '{automation_id}' not found in storage and no matching entries found in Entity Registry")
                except Exception as reg_error:
                    logger.warning(f"Failed to remove ghost automation from Entity Registry: {reg_error}")
                    raise Exception(f"Automation '{automation_id}' not found in storage and could not be removed from Entity Registry: {reg_error}")
            
            file_path = location['file_path']
            
            if location['location'] == 'automations.yaml':
                # Delete from automations.yaml
                content = await file_manager.read_file(file_path)
                automations = yaml.safe_load(content) or []
                automations = [auto for auto in automations if auto.get('id') != automation_id]
                new_content = yaml.dump(automations, allow_unicode=True, default_flow_style=False, sort_keys=False)
                await file_manager.write_file(file_path, new_content, create_backup=True)
                
            elif location['location'] == 'packages':
                # Delete from packages/*.yaml
                content = await file_manager.read_file(file_path)
                data = yaml.safe_load(content) or {}
                if location['format'] == 'list':
                    data['automation'] = [auto for auto in data['automation'] if auto.get('id') != automation_id]
                else:  # dict format
                    if location['key'] in data['automation']:
                        del data['automation'][location['key']]
                new_content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
                await file_manager.write_file(file_path, new_content, create_backup=True)
                
            elif location['location'] == 'storage':
                # Delete from .storage/automation.storage (JSON)
                content = await file_manager.read_file(file_path)
                storage_data = json.loads(content)
                storage_data['data']['automations'] = [auto for auto in storage_data['data']['automations'] if auto.get('id') != automation_id]
                new_content = json.dumps(storage_data, indent=2, ensure_ascii=False)
                await file_manager.write_file(file_path, new_content, create_backup=True)

            elif location['location'] == 'automations_dir':
                # Delete from automations/*.yaml (flat list format)
                content = await file_manager.read_file(file_path)
                automations = yaml.safe_load(content) or []
                automations = [auto for auto in automations if auto.get('id') != automation_id]
                new_content = yaml.dump(automations, allow_unicode=True, default_flow_style=False, sort_keys=False)
                await file_manager.write_file(file_path, new_content, create_backup=True)

            # Remove from Entity Registry - try to match by id, entity_id, and alias
            try:
                from app.services.ha_websocket import get_ws_client
                ws_client = await get_ws_client()
                
                # Get automation config to find alias
                automation_config = None
                try:
                    automation_config = await self.get_automation(automation_id)
                except Exception:
                    pass
                
                # Get Entity Registry to find all matching automations
                entity_registry = await ws_client.get_entity_registry_list()
                automation_entities = [e for e in entity_registry if e.get('entity_id', '').startswith('automation.')]
                
                # Get actual entity_id from location if available
                actual_entity_id = location.get('entity_id')
                if actual_entity_id and actual_entity_id.startswith('automation.'):
                    primary_entity_id = actual_entity_id
                else:
                    # Fallback to constructing from automation_id
                    primary_entity_id = f"automation.{automation_id}"
                
                # Get alias for matching
                automation_alias = None
                if automation_config:
                    automation_alias = automation_config.get('alias', '')
                
                # Normalize for matching
                automation_id_normalized = automation_id.lower().replace(' ', '_').replace('-', '_')
                alias_normalized = automation_alias.lower().replace(' ', '_').replace('-', '_') if automation_alias else None
                
                removed_entities = []
                for entity in automation_entities:
                    entity_id = entity.get('entity_id', '')
                    entity_name = entity.get('name', '')
                    
                    # Check if entity_id matches
                    if (entity_id == primary_entity_id or 
                        entity_id == f"automation.{automation_id}" or
                        entity_id.replace('automation.', '', 1) == automation_id):
                        try:
                            await ws_client.remove_entity_registry_entry(entity_id)
                            removed_entities.append(entity_id)
                            logger.debug(f"Removed automation from Entity Registry by id: {entity_id}")
                        except Exception as e:
                            logger.warning(f"Failed to remove {entity_id}: {e}")
                    
                    # Check if alias/name matches (exact match only to avoid false positives)
                    elif entity_name and (alias_normalized or automation_id_normalized):
                        entity_name_normalized = entity_name.lower().replace(' ', '_').replace('-', '_')
                        if ((alias_normalized and entity_name_normalized == alias_normalized) or
                            entity_name_normalized == automation_id_normalized):
                            try:
                                await ws_client.remove_entity_registry_entry(entity_id)
                                removed_entities.append(entity_id)
                                logger.debug(f"Removed automation from Entity Registry by alias: {entity_id} (name: {entity_name})")
                            except Exception as e:
                                logger.warning(f"Failed to remove {entity_id}: {e}")
                
                if not removed_entities:
                    # Fallback to primary entity_id if no matches found
                    try:
                        await ws_client.remove_entity_registry_entry(primary_entity_id)
                        logger.debug(f"Removed automation from Entity Registry: {primary_entity_id}")
                    except Exception as reg_error:
                        logger.warning(f"Failed to remove automation from Entity Registry: {reg_error}")
            except Exception as reg_error:
                logger.warning(f"Failed to remove automation from Entity Registry: {reg_error}")
            
            # Reload automations in Home Assistant
            try:
                from app.services.ha_websocket import get_ws_client
                ws_client = await get_ws_client()
                await ws_client.call_service('automation', 'reload')
                logger.info(f"Reloaded automations after deleting: {automation_id}")
            except Exception as reload_error:
                logger.warning(f"Failed to reload automations: {reload_error}. Automation deleted but may need manual reload.")
            
            logger.info(f"Deleted automation from {file_path}: {automation_id}")
            return {'success': True, 'automation_id': automation_id}
        except Exception as e:
            error_msg = str(e)
            if 'not found' in error_msg.lower():
                raise Exception(f"Automation not found: {automation_id}")
            logger.error(f"Failed to delete automation {automation_id}: {e}")
            raise
    
