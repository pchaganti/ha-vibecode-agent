"""Lovelace Dashboard Generator Service"""
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger('ha_cursor_agent')


class LovelaceGenerator:
    """Service for generating Lovelace dashboards"""
    
    # Card type mapping by entity domain
    DOMAIN_CARD_MAP = {
        'light': 'light',
        'switch': 'entities',
        'climate': 'thermostat',
        'cover': 'entities',
        'lock': 'entities',
        'fan': 'entities',
        'sensor': 'sensor',
        'binary_sensor': 'entities',
        'camera': 'picture-entity',
        'media_player': 'media-control',
        'weather': 'weather-forecast',
        'person': 'entity',
        'device_tracker': 'entity',
        'automation': 'entity',
        'script': 'entity',
        'scene': 'entity',
        'input_boolean': 'entity',
        'input_number': 'entity',
        'input_select': 'entity',
        'input_text': 'entity',
        'input_datetime': 'entity',
    }
    
    def __init__(self):
        """Initialize Lovelace Generator"""
        logger.info("LovelaceGenerator initialized")
    
    def analyze_entities(self, entities: List[Dict]) -> Dict[str, Any]:
        """
        Analyze entities and group them for dashboard generation
        
        Args:
            entities: List of entity dictionaries from HA
            
        Returns:
            Analysis with groupings by area, domain, and suggestions
        """
        logger.info(f"Analyzing {len(entities)} entities for dashboard generation")
        
        # Group by domain
        by_domain = defaultdict(list)
        # Group by area
        by_area = defaultdict(list)
        # Track entity types
        domain_counts = defaultdict(int)
        
        for entity in entities:
            entity_id = entity.get('entity_id', '')
            domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'
            
            # Count domains
            domain_counts[domain] += 1
            
            # Group by domain
            by_domain[domain].append(entity)
            
            # Group by area (if available)
            area = entity.get('attributes', {}).get('friendly_name', '')
            # Try to extract room from friendly_name (e.g., "Bedroom Light" -> "Bedroom")
            room = self._extract_room(area or entity_id)
            if room:
                by_area[room].append(entity)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(domain_counts, by_domain)
        
        analysis = {
            'total_entities': len(entities),
            'by_domain': {domain: len(ents) for domain, ents in by_domain.items()},
            'by_area': {area: len(ents) for area, ents in by_area.items()},
            'domain_counts': dict(domain_counts),
            'recommendations': recommendations,
            'grouped_entities': {
                'by_domain': dict(by_domain),
                'by_area': dict(by_area)
            }
        }
        
        logger.info(f"Analysis complete: {len(by_domain)} domains, {len(by_area)} areas")
        return analysis
    
    def _extract_room(self, name: str) -> Optional[str]:
        """Extract room name from entity friendly_name or entity_id"""
        # Common room names
        rooms = [
            'Living Room', 'Bedroom', 'Kitchen', 'Bathroom', 'Office',
            'Garage', 'Hallway', 'Dining Room', 'Guest Room', 'Basement',
            'Attic', 'Laundry', 'Balcony', 'Terrace', 'Garden',
            # Russian
            'Спальня', 'Гостиная', 'Кухня', 'Ванная', 'Офис',
            'Коридор', 'Гараж', 'Балкон'
        ]
        
        name_lower = name.lower()
        for room in rooms:
            if room.lower() in name_lower:
                return room
        
        return None
    
    def _generate_recommendations(self, domain_counts: Dict, by_domain: Dict) -> List[str]:
        """Generate dashboard recommendations based on entity analysis"""
        recommendations = []
        
        # Recommend views based on entity types
        if domain_counts.get('light', 0) > 3:
            recommendations.append("Create dedicated Lights view (you have many lights)")
        
        if domain_counts.get('climate', 0) > 0:
            recommendations.append("Add Climate Control view (thermostats/TRVs detected)")
        
        if domain_counts.get('media_player', 0) > 0:
            recommendations.append("Add Media view (media players detected)")
        
        if domain_counts.get('camera', 0) > 0:
            recommendations.append("Add Security view (cameras detected)")
        
        if domain_counts.get('sensor', 0) > 5:
            recommendations.append("Group sensors by type (many sensors detected)")
        
        if domain_counts.get('automation', 0) > 0 or domain_counts.get('script', 0) > 0:
            recommendations.append("Add Automation Management view")
        
        return recommendations
    
    def generate_dashboard(self, entities: List[Dict], style: str = 'modern') -> Dict[str, Any]:
        """
        Generate complete Lovelace dashboard configuration
        
        Args:
            entities: List of entities from HA
            style: Dashboard style ('modern', 'classic', 'minimal')
            
        Returns:
            Complete Lovelace dashboard configuration
        """
        logger.info(f"Generating {style} dashboard for {len(entities)} entities")
        
        # Analyze entities first
        analysis = self.analyze_entities(entities)
        by_domain = analysis['grouped_entities']['by_domain']
        by_area = analysis['grouped_entities']['by_area']
        
        # Generate views
        views = []
        
        # Home view (overview)
        home_view = self._generate_home_view(by_domain, style)
        views.append(home_view)
        
        # Lights view (if many lights)
        if len(by_domain.get('light', [])) > 3:
            lights_view = self._generate_lights_view(by_domain['light'], style)
            views.append(lights_view)
        
        # Climate view (if climate entities)
        if 'climate' in by_domain:
            climate_view = self._generate_climate_view(by_domain['climate'], style)
            views.append(climate_view)
        
        # Media view (if media players)
        if 'media_player' in by_domain:
            media_view = self._generate_media_view(by_domain['media_player'], style)
            views.append(media_view)
        
        # Sensors view (if many sensors)
        if len(by_domain.get('sensor', [])) > 5:
            sensors_view = self._generate_sensors_view(by_domain['sensor'], style)
            views.append(sensors_view)
        
        # Automation view (if automations/scripts)
        if 'automation' in by_domain or 'script' in by_domain:
            automation_view = self._generate_automation_view(by_domain, style)
            views.append(automation_view)
        
        dashboard_config = {
            'title': 'Home',
            'views': views
        }
        
        logger.info(f"Dashboard generated: {len(views)} views")
        return dashboard_config
    
    def _generate_home_view(self, by_domain: Dict, style: str) -> Dict:
        """Generate Home overview view"""
        cards = []
        
        # Weather card (if weather entity exists)
        if 'weather' in by_domain and len(by_domain['weather']) > 0:
            cards.append({
                'type': 'weather-forecast',
                'entity': by_domain['weather'][0]['entity_id'],
                'show_forecast': True
            })
        
        # Person cards
        if 'person' in by_domain:
            person_entities = [p['entity_id'] for p in by_domain['person']]
            cards.append({
                'type': 'entities',
                'title': 'People',
                'entities': person_entities
            })
        
        # Quick controls - lights
        if 'light' in by_domain:
            light_entities = [l['entity_id'] for l in by_domain['light'][:6]]  # Top 6
            cards.append({
                'type': 'light',
                'entities': light_entities,
                'title': 'Lights'
            })
        
        # Quick controls - climate
        if 'climate' in by_domain:
            climate_entities = [c['entity_id'] for c in by_domain['climate'][:4]]  # Top 4
            cards.append({
                'type': 'entities',
                'title': 'Climate',
                'entities': climate_entities
            })
        
        return {
            'title': 'Home',
            'path': 'home',
            'icon': 'mdi:home',
            'cards': cards
        }
    
    def _generate_lights_view(self, lights: List[Dict], style: str) -> Dict:
        """Generate Lights view"""
        light_entities = [l['entity_id'] for l in lights]
        
        return {
            'title': 'Lights',
            'path': 'lights',
            'icon': 'mdi:lightbulb',
            'cards': [
                {
                    'type': 'light',
                    'entities': light_entities
                }
            ]
        }
    
    def _generate_climate_view(self, climate: List[Dict], style: str) -> Dict:
        """Generate Climate Control view"""
        cards = []
        
        for entity in climate:
            cards.append({
                'type': 'thermostat',
                'entity': entity['entity_id']
            })
        
        return {
            'title': 'Climate',
            'path': 'climate',
            'icon': 'mdi:thermostat',
            'cards': cards
        }
    
    def _generate_media_view(self, media_players: List[Dict], style: str) -> Dict:
        """Generate Media view"""
        cards = []
        
        for player in media_players:
            cards.append({
                'type': 'media-control',
                'entity': player['entity_id']
            })
        
        return {
            'title': 'Media',
            'path': 'media',
            'icon': 'mdi:play',
            'cards': cards
        }
    
    def _generate_sensors_view(self, sensors: List[Dict], style: str) -> Dict:
        """Generate Sensors view"""
        # Group sensors by type
        by_type = defaultdict(list)
        
        for sensor in sensors:
            device_class = sensor.get('attributes', {}).get('device_class', 'other')
            by_type[device_class].append(sensor['entity_id'])
        
        cards = []
        
        # Create card for each sensor type
        for sensor_type, entity_ids in by_type.items():
            title = sensor_type.replace('_', ' ').title() if sensor_type != 'other' else 'Other Sensors'
            cards.append({
                'type': 'entities',
                'title': title,
                'entities': entity_ids
            })
        
        return {
            'title': 'Sensors',
            'path': 'sensors',
            'icon': 'mdi:gauge',
            'cards': cards
        }
    
    def _generate_automation_view(self, by_domain: Dict, style: str) -> Dict:
        """Generate Automation Management view"""
        entities = []
        
        if 'automation' in by_domain:
            entities.extend([a['entity_id'] for a in by_domain['automation']])
        
        if 'script' in by_domain:
            entities.extend([s['entity_id'] for s in by_domain['script']])
        
        return {
            'title': 'Automation',
            'path': 'automation',
            'icon': 'mdi:robot',
            'cards': [
                {
                    'type': 'entities',
                    'title': 'Automations & Scripts',
                    'entities': entities
                }
            ]
        }


# Global Lovelace generator instance
lovelace_generator = LovelaceGenerator()




