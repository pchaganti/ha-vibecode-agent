"""Home Assistant API Client"""
import os
import aiohttp
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger('ha_cursor_agent')

class HomeAssistantClient:
    """Client for Home Assistant API"""
    
    def __init__(self, token: str = None):
        self.url = os.getenv('HA_URL', 'http://supervisor/core')
        # Use provided token or fall back to environment token
        self.token = token or os.getenv('HA_TOKEN', '') or os.getenv('SUPERVISOR_TOKEN', '')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }
        
        # Debug logging
        token_source = "provided" if token else ("HA_TOKEN" if os.getenv('HA_TOKEN') else ("SUPERVISOR_TOKEN" if os.getenv('SUPERVISOR_TOKEN') else "none"))
        token_preview = f"{self.token[:20]}..." if self.token else "EMPTY"
        logger.info(f"HAClient initialized - URL: {self.url}, Token source: {token_source}, Token: {token_preview}")
    
    def set_token(self, token: str):
        """Update token for requests"""
        self.token = token
        self.headers['Authorization'] = f'Bearer {token}'
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        suppress_404_logging: bool = False
    ) -> Dict:
        """Make HTTP request to HA API
        
        Args:
            suppress_404_logging: If True, 404 errors will be logged as DEBUG instead of ERROR
        """
        url = f"{self.url}/api/{endpoint}"
        
        # For POST requests, aiohttp handles query params correctly via params argument
        # No need to manually append to URL - let aiohttp handle it
        
        # Use custom timeout or default 240 seconds (4 minutes)
        # Long operations like backup_full, file operations, and Git cleanup need more time
        timeout_seconds = timeout if timeout is not None else 240
        
        # Debug logging
        token_preview = f"{self.token[:20]}..." if self.token else "EMPTY"
        logger.info(f"HA API Request: {method} {url}, Data: {data}, Params: {params}, Timeout: {timeout_seconds}s")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, 
                    url, 
                    headers=self.headers, 
                    json=data,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as response:
                    if response.status >= 400:
                        text = await response.text()
                        # 404 is often expected (entity not found), log as DEBUG if suppressed
                        if response.status == 404 and suppress_404_logging:
                            logger.debug(f"HA API 404 (expected): {text} | URL: {url}")
                        else:
                            logger.error(f"HA API error: {response.status} - {text} | URL: {url} | Data: {data} | Params: {params} | Token used: {token_preview}")
                        raise Exception(f"HA API error: {response.status} - {text}")
                    
                    logger.debug(f"HA API success: {method} {url} -> {response.status}")
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Connection error to HA: {e}")
            raise Exception(f"Failed to connect to Home Assistant: {e}")
    
    async def get_states(self) -> List[Dict]:
        """Get all entity states"""
        return await self._request('GET', 'states')
    
    async def get_state(self, entity_id: str, suppress_404_logging: bool = False) -> Dict:
        """Get specific entity state
        
        Args:
            entity_id: Entity ID to get state for
            suppress_404_logging: If True, 404 errors will be logged as DEBUG instead of ERROR
        """
        return await self._request('GET', f'states/{entity_id}', suppress_404_logging=suppress_404_logging)
    
    async def get_services(self) -> List[Dict]:
        """Get all available services"""
        return await self._request('GET', 'services')
    
    async def call_service(self, domain: str, service: str, data: Dict) -> Dict:
        """Call a Home Assistant service"""
        endpoint = f"services/{domain}/{service}"
        
        # Some services need special handling
        params = None
        timeout = None
        
        if domain == 'hassio' and service in ['backup_full', 'backup_partial', 'restore_full', 'restore_partial']:
            # Long-running operations need more time
            timeout = 300  # 5 minutes for backup/restore operations
        
        return await self._request('POST', endpoint, data, params=params, timeout=timeout)
    
    async def get_config(self) -> Dict:
        """Get HA configuration"""
        return await self._request('GET', 'config')
    
    async def check_config(self) -> Dict:
        """Check configuration validity"""
        return await self.call_service('homeassistant', 'check_config', {})
    
    async def reload_component(self, component: str) -> Dict:
        """Reload a specific component"""
        component_map = {
            'automations': ('automation', 'reload'),
            'scripts': ('script', 'reload'),
            'templates': ('template', 'reload'),
            'core': ('homeassistant', 'reload_core_config'),
            'all': ('homeassistant', 'reload_all')
        }
        
        if component not in component_map:
            raise ValueError(f"Unknown component: {component}")
        
        domain, service = component_map[component]
        return await self.call_service(domain, service, {})
    
    async def restart(self) -> Dict:
        """Restart Home Assistant"""
        return await self.call_service('homeassistant', 'restart', {})

    async def get_logbook_entries(
        self,
        start_time: str,
        end_time: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> List[Dict]:
        """Fetch logbook entries from Home Assistant"""
        if not start_time:
            raise ValueError("start_time is required for logbook queries")
        
        params: Dict[str, Any] = {}
        if end_time:
            params['end_time'] = end_time
        if entity_id:
            params['entity'] = entity_id
        
        return await self._request('GET', f'logbook/{start_time}', params=params)
    
    async def rename_entity(self, old_entity_id: str, new_entity_id: str, new_name: Optional[str] = None) -> Dict:
        """
        Rename an entity_id via Entity Registry WebSocket API
        
        Args:
            old_entity_id: Current entity_id (e.g., 'climate.sonoff_trvzb_thermostat')
            new_entity_id: New entity_id (e.g., 'climate.office_trv_thermostat')
            new_name: Optional new friendly name
            
        Returns:
            Entity registry update result
            
        Raises:
            Exception: If rename fails or WebSocket not available
        """
        # Import here to avoid circular dependency
        from app.services.ha_websocket import get_ws_client
        
        logger.info(f"Renaming entity: {old_entity_id} → {new_entity_id}")
        
        try:
            ws_client = await get_ws_client()
            
            message = {
                'type': 'config/entity_registry/update',
                'entity_id': old_entity_id,
                'new_entity_id': new_entity_id
            }
            
            if new_name:
                message['name'] = new_name
            
            result = await ws_client._send_message(message)
            logger.info(f"✅ Successfully renamed entity: {old_entity_id} → {new_entity_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to rename entity via WebSocket: {e}")
            raise Exception(f"Failed to rename entity {old_entity_id} to {new_entity_id}: {e}")
    
    # ==================== Automation API ====================
    
    async def list_automations(self) -> List[Dict]:
        """
        List all automations from Home Assistant (via REST API)
        
        Returns all automations that HA has loaded, regardless of source:
        - From automations.yaml
        - From packages/*.yaml
        - Created via UI (stored in .storage)
        
        Returns:
            List of automation configurations
        """
        try:
            result = await self._request('GET', 'config/automation/config')
            # HA returns a dict where keys are automation_ids and values are configs
            if isinstance(result, dict):
                automations = []
                for automation_id, config in result.items():
                    # Ensure 'id' field is present
                    automation = dict(config) if isinstance(config, dict) else config
                    if 'id' not in automation:
                        automation['id'] = automation_id
                    automations.append(automation)
                return automations
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Failed to list automations via API: {e}")
            raise
    
    async def get_automation(self, automation_id: str) -> Dict:
        """
        Get single automation configuration by ID
        
        Args:
            automation_id: Automation ID
            
        Returns:
            Automation configuration dict
        """
        try:
            result = await self._request('GET', f'config/automation/config/{automation_id}', suppress_404_logging=True)
            # Ensure 'id' field is present
            if isinstance(result, dict) and 'id' not in result:
                result['id'] = automation_id
            return result
        except Exception as e:
            error_msg = str(e)
            if '404' in error_msg or 'not found' in error_msg.lower():
                raise Exception(f"Automation not found: {automation_id}")
            logger.error(f"Failed to get automation {automation_id} via API: {e}")
            raise
    
    async def create_automation(self, automation_config: Dict) -> Dict:
        """
        Create new automation via REST API
        
        Args:
            automation_config: Automation configuration dict (must include 'id')
            
        Returns:
            Created automation configuration
        """
        automation_id = automation_config.get('id')
        if not automation_id:
            raise ValueError("Automation config must include 'id' field")
        
        try:
            result = await self._request('POST', f'config/automation/config/{automation_id}', data=automation_config)
            logger.info(f"Created automation via API: {automation_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create automation {automation_id} via API: {e}")
            raise
    
    async def update_automation(self, automation_id: str, automation_config: Dict) -> Dict:
        """
        Update existing automation via REST API
        
        Args:
            automation_id: Automation ID
            automation_config: Updated automation configuration
            
        Returns:
            Updated automation configuration
        """
        try:
            # Ensure 'id' matches
            config = dict(automation_config)
            config['id'] = automation_id
            result = await self._request('POST', f'config/automation/config/{automation_id}', data=config)
            logger.info(f"Updated automation via API: {automation_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to update automation {automation_id} via API: {e}")
            raise
    
    async def delete_automation(self, automation_id: str) -> Dict:
        """
        Delete automation via REST API
        
        Args:
            automation_id: Automation ID to delete
            
        Returns:
            Deletion result
        """
        try:
            result = await self._request('DELETE', f'config/automation/config/{automation_id}')
            logger.info(f"Deleted automation via API: {automation_id}")
            return result
        except Exception as e:
            error_msg = str(e)
            if '404' in error_msg or 'not found' in error_msg.lower():
                raise Exception(f"Automation not found: {automation_id}")
            logger.error(f"Failed to delete automation {automation_id} via API: {e}")
            raise
    
    # ==================== Script API ====================
    
    async def list_scripts(self) -> Dict[str, Dict]:
        """
        List all scripts from Home Assistant (via REST API)
        
        Returns all scripts that HA has loaded, regardless of source.
        
        Returns:
            Dict where keys are script_ids and values are script configs
        """
        try:
            result = await self._request('GET', 'config/script/config')
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Failed to list scripts via API: {e}")
            raise
    
    async def get_script(self, script_id: str) -> Dict:
        """
        Get single script configuration by ID
        
        Args:
            script_id: Script ID
            
        Returns:
            Script configuration dict
        """
        try:
            result = await self._request('GET', f'config/script/config/{script_id}', suppress_404_logging=True)
            return result
        except Exception as e:
            error_msg = str(e)
            if '404' in error_msg or 'not found' in error_msg.lower():
                raise Exception(f"Script not found: {script_id}")
            logger.error(f"Failed to get script {script_id} via API: {e}")
            raise
    
    async def create_script(self, script_id: str, script_config: Dict) -> Dict:
        """
        Create new script via REST API
        
        Args:
            script_id: Script ID
            script_config: Script configuration dict
            
        Returns:
            Created script configuration
        """
        try:
            result = await self._request('POST', f'config/script/config/{script_id}', data=script_config)
            logger.info(f"Created script via API: {script_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create script {script_id} via API: {e}")
            raise
    
    async def update_script(self, script_id: str, script_config: Dict) -> Dict:
        """
        Update existing script via REST API
        
        Args:
            script_id: Script ID
            script_config: Updated script configuration
            
        Returns:
            Updated script configuration
        """
        try:
            result = await self._request('POST', f'config/script/config/{script_id}', data=script_config)
            logger.info(f"Updated script via API: {script_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to update script {script_id} via API: {e}")
            raise
    
    async def delete_script(self, script_id: str) -> Dict:
        """
        Delete script via REST API
        
        Args:
            script_id: Script ID to delete
            
        Returns:
            Deletion result
        """
        try:
            result = await self._request('DELETE', f'config/script/config/{script_id}')
            logger.info(f"Deleted script via API: {script_id}")
            return result
        except Exception as e:
            error_msg = str(e)
            if '404' in error_msg or 'not found' in error_msg.lower():
                raise Exception(f"Script not found: {script_id}")
            logger.error(f"Failed to delete script {script_id} via API: {e}")
            raise

# Global client instance
ha_client = HomeAssistantClient()

