"""Script CRUD operations mixin for HomeAssistantClient"""
import logging
from typing import Dict, List

logger = logging.getLogger('ha_cursor_agent')


class ScriptMixin:
    """Mixin providing script CRUD methods. Requires _request() from base class."""

    async def list_scripts(self) -> Dict[str, Dict]:
        """
        List all scripts from Home Assistant (via Entity Registry + file system)
        
        Returns all scripts that HA has loaded, regardless of source.
        
        Note: Home Assistant doesn't provide WebSocket API for listing scripts.
        We use Entity Registry to get all script entities, then collect their
        configurations from files and .storage.
        
        Returns:
            Dict where keys are script_ids and values are script configs
        """
        try:
            # Import here to avoid circular dependency
            from app.services.ha_websocket import get_ws_client
            from app.services.file_manager import file_manager
            import json
            import yaml
            from pathlib import Path
            
            # Get all script entities from Entity Registry
            ws_client = await get_ws_client()
            entity_registry = await ws_client.get_entity_registry_list()
            
            # Filter script entities
            script_entities = [
                e for e in entity_registry 
                if e.get('entity_id', '').startswith('script.')
            ]
            
            # Cache for script configurations (read files ONCE at the beginning)
            script_cache = {}
            
            # Read all script files ONCE at the beginning
            try:
                # Read scripts.yaml
                try:
                    content = await file_manager.read_file('scripts.yaml', suppress_not_found_logging=True)
                    file_scripts = yaml.safe_load(content) or {}
                    if isinstance(file_scripts, dict):
                        script_cache.update(file_scripts)
                except Exception:
                    pass
                
                # Read packages/*.yaml files
                try:
                    packages_dir = file_manager.config_path / 'packages'
                    if packages_dir.exists():
                        for yaml_file in packages_dir.rglob('*.yaml'):
                            try:
                                content = yaml_file.read_text(encoding='utf-8')
                                data = yaml.safe_load(content)
                                if isinstance(data, dict) and 'script' in data:
                                    pkg_scripts = data['script']
                                    if isinstance(pkg_scripts, dict):
                                        script_cache.update(pkg_scripts)
                            except Exception:
                                continue
                except Exception:
                    pass
                
                # Read scripts/*.yaml files (for !include_dir_merge_named scripts/)
                try:
                    scripts_dir = file_manager.config_path / 'scripts'
                    if scripts_dir.exists() and scripts_dir.is_dir():
                        for yaml_file in scripts_dir.rglob('*.yaml'):
                            try:
                                content = yaml_file.read_text(encoding='utf-8')
                                data = yaml.safe_load(content)
                                if isinstance(data, dict):
                                    for sid, sconfig in data.items():
                                        if sid not in script_cache:
                                            script_cache[sid] = sconfig
                            except Exception:
                                continue
                except Exception:
                    pass

                # Read .storage/script.storage (UI-created scripts)
                try:
                    storage_file = file_manager.config_path / '.storage' / 'script.storage'
                    if storage_file.exists():
                        content = storage_file.read_text(encoding='utf-8')
                        storage_data = json.loads(content)
                        if 'data' in storage_data and 'scripts' in storage_data['data']:
                            storage_scripts = storage_data['data']['scripts']
                            if isinstance(storage_scripts, dict):
                                script_cache.update(storage_scripts)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Failed to read scripts from files: {e}")
            
            scripts = {}
            script_ids_seen = set()
            
            # Get script IDs from entity registry and use cache (no file reads here)
            for entity in script_entities:
                entity_id = entity.get('entity_id', '')
                if not entity_id.startswith('script.'):
                    continue
                
                # Extract script_id from entity_id (script.xxx -> xxx)
                script_id = entity_id.replace('script.', '', 1)
                
                if script_id in script_ids_seen:
                    continue
                script_ids_seen.add(script_id)
                
                # Use cached config if available, otherwise empty dict
                if script_id in script_cache:
                    scripts[script_id] = script_cache[script_id]
                else:
                    # Script in registry but not in files - might be UI-created
                    scripts[script_id] = {}
            
            # Also add scripts from cache that weren't in entity registry
            for script_id, script_config in script_cache.items():
                if script_id not in script_ids_seen:
                    scripts[script_id] = script_config
                    script_ids_seen.add(script_id)
            
            return scripts
            
        except Exception as e:
            logger.error(f"Failed to list scripts: {e}")
            raise
    
    async def get_script(self, script_id: str) -> Dict:
        """
        Get single script configuration by ID (via files + .storage)
        
        Args:
            script_id: Script ID
            
        Returns:
            Script configuration dict
        """
        try:
            from app.services.file_manager import file_manager
            import yaml
            import json
            from pathlib import Path
            
            # Try to find in scripts.yaml
            try:
                content = await file_manager.read_file('scripts.yaml', suppress_not_found_logging=True)
                scripts = yaml.safe_load(content) or {}
                if isinstance(scripts, dict) and script_id in scripts:
                    return scripts[script_id]
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
                            if isinstance(data, dict) and 'script' in data:
                                pkg_scripts = data['script']
                                if isinstance(pkg_scripts, dict) and script_id in pkg_scripts:
                                    return pkg_scripts[script_id]
                        except Exception:
                            continue
            except Exception:
                pass

            # Try to find in scripts/*.yaml (for !include_dir_merge_named scripts/)
            try:
                scripts_dir = file_manager.config_path / 'scripts'
                if scripts_dir.exists() and scripts_dir.is_dir():
                    for yaml_file in scripts_dir.rglob('*.yaml'):
                        try:
                            content = yaml_file.read_text(encoding='utf-8')
                            data = yaml.safe_load(content)
                            if isinstance(data, dict) and script_id in data:
                                return data[script_id]
                        except Exception:
                            continue
            except Exception:
                pass

            # Try to find in .storage (UI-created scripts)
            try:
                storage_file = file_manager.config_path / '.storage' / 'script.storage'
                if storage_file.exists():
                    content = storage_file.read_text(encoding='utf-8')
                    storage_data = json.loads(content)
                    if 'data' in storage_data and 'scripts' in storage_data['data']:
                        scripts_dict = storage_data['data']['scripts']
                        # Check by script_id (key in dict)
                        if script_id in scripts_dict:
                            return scripts_dict[script_id]
                        # Also check by entity_id if script_id doesn't match
                        # (scripts in storage are keyed by script_id, but Entity Registry may use different entity_id)
                        for key, script_config in scripts_dict.items():
                            if isinstance(script_config, dict):
                                entity_id = script_config.get('entity_id', '')
                                if entity_id:
                                    if entity_id.startswith('script.'):
                                        entity_id_clean = entity_id.replace('script.', '', 1)
                                    else:
                                        entity_id_clean = entity_id
                                    if entity_id_clean == script_id or entity_id == script_id:
                                        return script_config
            except Exception:
                pass
            
            raise Exception(f"Script not found: {script_id}")
            
        except Exception as e:
            error_msg = str(e)
            if 'not found' in error_msg.lower():
                raise Exception(f"Script not found: {script_id}")
            logger.error(f"Failed to get script {script_id}: {e}")
            raise
    
    async def create_script(self, script_id: str, script_config: Dict) -> Dict:
        """
        Create new script via Home Assistant REST API
        
        Uses POST /api/config/script/config/{script_id} endpoint.
        Home Assistant automatically determines where to store the script
        (scripts.yaml, packages/*, or .storage).
        
        Args:
            script_id: Script ID
            script_config: Script configuration dict
            
        Returns:
            Created script configuration
        """
        try:
            # Use REST API endpoint: POST /api/config/script/config/{script_id}
            endpoint = f"config/script/config/{script_id}"
            
            result = await self._request('POST', endpoint, data=script_config)
            
            logger.info(f"Created script via REST API: {script_id}")
            return result
        except Exception as e:
            error_msg = str(e)
            if '409' in error_msg or 'already exists' in error_msg.lower():
                raise ValueError(f"Script with ID '{script_id}' already exists")
            logger.error(f"Failed to create script {script_id} via REST API: {e}")
            raise
    
    async def update_script(self, script_id: str, script_config: Dict) -> Dict:
        """
        Update existing script via Home Assistant REST API
        
        Uses POST /api/config/script/config/{script_id} endpoint.
        Home Assistant automatically updates the script in its original location.
        
        Args:
            script_id: Script ID
            script_config: Updated script configuration
            
        Returns:
            Updated script configuration
        """
        try:
            # Use REST API endpoint: POST /api/config/script/config/{script_id}
            endpoint = f"config/script/config/{script_id}"
            
            result = await self._request('POST', endpoint, data=script_config)
            
            logger.info(f"Updated script via REST API: {script_id}")
            return result
        except Exception as e:
            error_msg = str(e)
            if '404' in error_msg or 'not found' in error_msg.lower():
                raise Exception(f"Script '{script_id}' not found")
            logger.error(f"Failed to update script {script_id} via REST API: {e}")
            raise
    
    async def _find_script_location(self, script_id: str) -> Dict:
        """
        Find where a script is stored (scripts.yaml, packages/*.yaml, or .storage)
        
        Checks both script_id (as dict key) and entity_id (if present in script config)
        to handle cases where Entity Registry entity_id differs from script_id.
        
        Returns:
            Dict with keys: 'location' ('scripts.yaml', 'packages', or 'storage'),
                           'file_path' (relative path), 'entity_id' (if found)
        """
        from app.services.file_manager import file_manager
        import yaml
        import json
        from pathlib import Path
        
        # Helper to check if script matches
        def matches_script(script_key, script_config, target_id):
            # Check by key (script_id)
            if script_key == target_id:
                return True
            # Also check entity_id if present in config
            if isinstance(script_config, dict):
                entity_id = script_config.get('entity_id', '')
                if entity_id:
                    if entity_id.startswith('script.'):
                        entity_id_clean = entity_id.replace('script.', '', 1)
                    else:
                        entity_id_clean = entity_id
                    if entity_id_clean == target_id or entity_id == target_id:
                        return True
            return False
        
        # Try scripts.yaml
        try:
            content = await file_manager.read_file('scripts.yaml', suppress_not_found_logging=True)
            scripts = yaml.safe_load(content) or {}
            if isinstance(scripts, dict):
                if script_id in scripts:
                    result = {'location': 'scripts.yaml', 'file_path': 'scripts.yaml'}
                    script_config = scripts[script_id]
                    if isinstance(script_config, dict) and script_config.get('entity_id'):
                        result['entity_id'] = script_config.get('entity_id')
                    return result
                # Also check by entity_id
                for key, script_config in scripts.items():
                    if matches_script(key, script_config, script_id):
                        result = {'location': 'scripts.yaml', 'file_path': 'scripts.yaml'}
                        if isinstance(script_config, dict) and script_config.get('entity_id'):
                            result['entity_id'] = script_config.get('entity_id')
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
                        if isinstance(data, dict) and 'script' in data:
                            pkg_scripts = data['script']
                            rel_path = yaml_file.relative_to(file_manager.config_path)
                            
                            if isinstance(pkg_scripts, dict):
                                if script_id in pkg_scripts:
                                    result = {'location': 'packages', 'file_path': str(rel_path)}
                                    script_config = pkg_scripts[script_id]
                                    if isinstance(script_config, dict) and script_config.get('entity_id'):
                                        result['entity_id'] = script_config.get('entity_id')
                                    return result
                                # Also check by entity_id
                                for key, script_config in pkg_scripts.items():
                                    if matches_script(key, script_config, script_id):
                                        result = {'location': 'packages', 'file_path': str(rel_path)}
                                        if isinstance(script_config, dict) and script_config.get('entity_id'):
                                            result['entity_id'] = script_config.get('entity_id')
                                        return result
                    except Exception:
                        continue
        except Exception:
            pass

        # Try scripts/*.yaml (for !include_dir_merge_named scripts/)
        try:
            scripts_dir = file_manager.config_path / 'scripts'
            if scripts_dir.exists() and scripts_dir.is_dir():
                for yaml_file in scripts_dir.rglob('*.yaml'):
                    try:
                        content = yaml_file.read_text(encoding='utf-8')
                        data = yaml.safe_load(content)
                        if isinstance(data, dict):
                            for key, script_config in data.items():
                                if matches_script(key, script_config, script_id):
                                    rel_path = yaml_file.relative_to(file_manager.config_path)
                                    result = {'location': 'scripts_dir', 'file_path': str(rel_path)}
                                    if isinstance(script_config, dict) and script_config.get('entity_id'):
                                        result['entity_id'] = script_config.get('entity_id')
                                    return result
                    except Exception:
                        continue
        except Exception:
            pass

        # Try .storage (UI-created)
        try:
            storage_file = file_manager.config_path / '.storage' / 'script.storage'
            if storage_file.exists():
                content = storage_file.read_text(encoding='utf-8')
                storage_data = json.loads(content)
                if 'data' in storage_data and 'scripts' in storage_data['data']:
                    scripts_dict = storage_data['data']['scripts']
                    if script_id in scripts_dict:
                        result = {'location': 'storage', 'file_path': '.storage/script.storage'}
                        script_config = scripts_dict[script_id]
                        if isinstance(script_config, dict) and script_config.get('entity_id'):
                            result['entity_id'] = script_config.get('entity_id')
                        return result
                    # Also check by entity_id
                    for key, script_config in scripts_dict.items():
                        if matches_script(key, script_config, script_id):
                            result = {'location': 'storage', 'file_path': '.storage/script.storage'}
                            if isinstance(script_config, dict) and script_config.get('entity_id'):
                                result['entity_id'] = script_config.get('entity_id')
                            return result
        except Exception:
            pass
        
        return None
    
    async def delete_script(self, script_id: str) -> Dict:
        """
        Delete script from its original location (file-based approach)
        
        Note: Home Assistant REST API does not support DELETE method for scripts
        (only works for UI-created scripts, returns 405 for YAML-defined ones).
        We find where the script is stored and remove it from there, then remove
        from Entity Registry and reload scripts.
        
        Args:
            script_id: Script ID to delete
            
        Returns:
            Deletion result
        """
        try:
            from app.services.file_manager import file_manager
            import yaml
            import json
            
            # Find where script is located
            location = await self._find_script_location(script_id)
            if not location:
                raise Exception(f"Script '{script_id}' not found")
            
            file_path = location['file_path']
            
            if location['location'] == 'scripts.yaml':
                # Delete from scripts.yaml
                content = await file_manager.read_file(file_path)
                scripts = yaml.safe_load(content) or {}
                if script_id in scripts:
                    del scripts[script_id]
                new_content = yaml.dump(scripts, allow_unicode=True, default_flow_style=False, sort_keys=False)
                await file_manager.write_file(file_path, new_content, create_backup=True)
                
            elif location['location'] == 'packages':
                # Delete from packages/*.yaml
                content = await file_manager.read_file(file_path)
                data = yaml.safe_load(content) or {}
                if 'script' in data and script_id in data['script']:
                    del data['script'][script_id]
                new_content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
                await file_manager.write_file(file_path, new_content, create_backup=True)
                
            elif location['location'] == 'storage':
                # Delete from .storage/script.storage (JSON)
                content = await file_manager.read_file(file_path)
                storage_data = json.loads(content)
                if 'data' in storage_data and 'scripts' in storage_data['data']:
                    if script_id in storage_data['data']['scripts']:
                        del storage_data['data']['scripts'][script_id]
                new_content = json.dumps(storage_data, indent=2, ensure_ascii=False)
                await file_manager.write_file(file_path, new_content, create_backup=True)

            elif location['location'] == 'scripts_dir':
                # Delete from scripts/*.yaml (named dict format)
                content = await file_manager.read_file(file_path)
                data = yaml.safe_load(content) or {}
                if script_id in data:
                    del data[script_id]
                new_content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
                await file_manager.write_file(file_path, new_content, create_backup=True)

            # Remove from Entity Registry
            # Use actual entity_id from location if found, otherwise construct from script_id
            try:
                from app.services.ha_websocket import get_ws_client
                ws_client = await get_ws_client()
                # Get actual entity_id from location if available
                actual_entity_id = location.get('entity_id')
                if actual_entity_id and actual_entity_id.startswith('script.'):
                    entity_id = actual_entity_id
                else:
                    # Fallback to constructing from script_id
                    entity_id = f"script.{script_id}"
                await ws_client.remove_entity_registry_entry(entity_id)
                logger.debug(f"Removed script from Entity Registry: {entity_id}")
            except Exception as reg_error:
                logger.warning(f"Failed to remove script from Entity Registry: {reg_error}")
            
            # Reload scripts in Home Assistant
            try:
                from app.services.ha_websocket import get_ws_client
                ws_client = await get_ws_client()
                await ws_client.call_service('script', 'reload')
                logger.info(f"Reloaded scripts after deleting: {script_id}")
            except Exception as reload_error:
                logger.warning(f"Failed to reload scripts: {reload_error}. Script deleted but may need manual reload.")
            
            logger.info(f"Deleted script from {file_path}: {script_id}")
            return {'success': True, 'script_id': script_id}
        except Exception as e:
            error_msg = str(e)
            if 'not found' in error_msg.lower():
                raise Exception(f"Script not found: {script_id}")
            logger.error(f"Failed to delete script {script_id}: {e}")
            raise

