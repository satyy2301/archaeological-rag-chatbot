"""
Smart Field Assistant Module
Context-aware field help, automated documentation, and safety features
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartFieldAssistant:
    """Provides context-aware assistance for field work."""
    
    def __init__(self, data_directory: str = "./field_data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        self.field_notes_file = self.data_directory / "field_notes.json"
        self.resources_file = self.data_directory / "resources.json"
        self.safety_file = self.data_directory / "safety_protocols.json"
        self._initialize_default_data()
    
    def _initialize_default_data(self):
        """Initialize default field data."""
        if not self.resources_file.exists():
            default_resources = {
                'artifact_bags': 50,
                'markers': 30,
                'tape_measures': 5,
                'compass': 2,
                'camera_batteries': 4,
                'field_forms': 100,
            }
            with open(self.resources_file, 'w') as f:
                json.dump(default_resources, f, indent=2)
        
        if not self.safety_file.exists():
            default_safety = {
                'emergency_contacts': [],
                'first_aid_location': '',
                'hazard_log': [],
                'safety_protocols': self._get_default_safety_protocols()
            }
            with open(self.safety_file, 'w') as f:
                json.dump(default_safety, f, indent=2)
    
    def _get_default_safety_protocols(self) -> List[Dict]:
        """Get default safety protocols."""
        return [
            {
                'title': 'Site Safety',
                'content': 'Always wear appropriate safety equipment. Be aware of site hazards.'
            },
            {
                'title': 'Weather Conditions',
                'content': 'Check weather forecast. Secure equipment in case of severe weather.'
            },
            {
                'title': 'Emergency Procedures',
                'content': 'Know emergency contact numbers. Have first aid kit accessible.'
            },
            {
                'title': 'Team Communication',
                'content': 'Maintain regular check-ins. Share location with team members.'
            }
        ]
    
    def get_context_aware_alerts(self, current_location: Optional[Dict] = None,
                                 weather_data: Optional[Dict] = None,
                                 time: Optional[datetime] = None) -> List[Dict]:
        """Get context-aware alerts based on location, weather, and time."""
        alerts = []
        
        if not time:
            time = datetime.now()
        
        # Time-based reminders
        if time.hour == 17:  # 5 PM
            alerts.append({
                'type': 'reminder',
                'priority': 'medium',
                'title': 'Photo Log Due',
                'message': 'Remember to complete today\'s photo log before end of day.',
                'timestamp': time.isoformat()
            })
        
        # Weather alerts (if provided)
        if weather_data:
            if weather_data.get('rain_forecast', {}).get('hours_ahead', 999) <= 2:
                alerts.append({
                    'type': 'warning',
                    'priority': 'high',
                    'title': 'Rain Alert',
                    'message': f"Rain expected in {weather_data['rain_forecast']['hours_ahead']} hours. Cover trenches and secure equipment.",
                    'timestamp': time.isoformat()
                })
            
            if weather_data.get('temperature', 0) > 35:
                alerts.append({
                    'type': 'warning',
                    'priority': 'medium',
                    'title': 'Heat Warning',
                    'message': 'High temperature. Ensure adequate hydration and rest breaks.',
                    'timestamp': time.isoformat()
                })
        
        # Resource tracking alerts
        resources = self.get_resource_status()
        for resource, count in resources.items():
            if count < 10:
                alerts.append({
                    'type': 'warning',
                    'priority': 'medium',
                    'title': f'{resource.replace("_", " ").title()} Running Low',
                    'message': f'Only {count} {resource.replace("_", " ")} remaining. Consider restocking.',
                    'timestamp': time.isoformat()
                })
        
        # Location-based alerts (if GPS data available)
        if current_location:
            # Could check against known sites, hazards, etc.
            pass
        
        return alerts
    
    def record_field_note(self, note_text: str, note_type: str = 'general',
                         location: Optional[Dict] = None,
                         photos: Optional[List[str]] = None,
                         tags: Optional[List[str]] = None) -> Dict:
        """Record a field note."""
        field_note = {
            'id': f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'type': note_type,
            'text': note_text,
            'location': location or {},
            'photos': photos or [],
            'tags': tags or []
        }
        
        # Load existing notes
        notes = self.get_field_notes()
        notes.append(field_note)
        
        # Save notes
        with open(self.field_notes_file, 'w') as f:
            json.dump(notes, f, indent=2, default=str)
        
        logger.info(f"Field note recorded: {field_note['id']}")
        return field_note
    
    def get_field_notes(self, date: Optional[datetime] = None) -> List[Dict]:
        """Get field notes, optionally filtered by date."""
        if self.field_notes_file.exists():
            with open(self.field_notes_file, 'r') as f:
                notes = json.load(f)
        else:
            notes = []
        
        if date:
            date_str = date.strftime('%Y-%m-%d')
            notes = [n for n in notes if n.get('timestamp', '').startswith(date_str)]
        
        return sorted(notes, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def get_resource_status(self) -> Dict[str, int]:
        """Get current resource inventory status."""
        if self.resources_file.exists():
            with open(self.resources_file, 'r') as f:
                return json.load(f)
        return {}
    
    def update_resource(self, resource_name: str, change: int):
        """Update resource count (positive to add, negative to use)."""
        resources = self.get_resource_status()
        current_count = resources.get(resource_name, 0)
        resources[resource_name] = max(0, current_count + change)
        
        with open(self.resources_file, 'w') as f:
            json.dump(resources, f, indent=2)
        
        logger.info(f"Resource updated: {resource_name} = {resources[resource_name]}")
    
    def log_hazard(self, hazard_type: str, description: str, location: Optional[Dict] = None,
                   severity: str = 'medium') -> Dict:
        """Log a site hazard."""
        hazard = {
            'id': f"hazard_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'type': hazard_type,
            'description': description,
            'location': location or {},
            'severity': severity,
            'resolved': False
        }
        
        # Load existing hazards
        safety_data = self._load_safety_data()
        safety_data['hazard_log'].append(hazard)
        
        with open(self.safety_file, 'w') as f:
            json.dump(safety_data, f, indent=2, default=str)
        
        logger.info(f"Hazard logged: {hazard['id']}")
        return hazard
    
    def get_hazards(self, unresolved_only: bool = True) -> List[Dict]:
        """Get logged hazards."""
        safety_data = self._load_safety_data()
        hazards = safety_data.get('hazard_log', [])
        
        if unresolved_only:
            hazards = [h for h in hazards if not h.get('resolved', False)]
        
        return sorted(hazards, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def get_safety_protocols(self) -> List[Dict]:
        """Get safety protocols."""
        safety_data = self._load_safety_data()
        return safety_data.get('safety_protocols', [])
    
    def _load_safety_data(self) -> Dict:
        """Load safety data."""
        if self.safety_file.exists():
            with open(self.safety_file, 'r') as f:
                return json.load(f)
        return {'emergency_contacts': [], 'hazard_log': [], 'safety_protocols': []}
    
    def create_daily_log_template(self, date: Optional[datetime] = None) -> Dict:
        """Create a daily log template."""
        if not date:
            date = datetime.now()
        
        template = {
            'date': date.strftime('%Y-%m-%d'),
            'weather': '',
            'team_members': [],
            'activities': [],
            'findings': [],
            'photos_taken': 0,
            'artifacts_recorded': 0,
            'issues': [],
            'notes': ''
        }
        
        return template
    
    def enrich_photo_metadata(self, photo_path: str, location: Optional[Dict] = None,
                             context: Optional[str] = None,
                             trench: Optional[str] = None,
                             locus: Optional[str] = None) -> Dict:
        """Enrich photo with metadata for field documentation."""
        metadata = {
            'photo_path': photo_path,
            'timestamp': datetime.now().isoformat(),
            'location': location or {},
            'context': context or '',
            'trench': trench or '',
            'locus': locus or '',
            'tags': []
        }
        
        # Add tags based on context
        if trench:
            metadata['tags'].append(f'trench_{trench}')
        if locus:
            metadata['tags'].append(f'locus_{locus}')
        if context:
            metadata['tags'].append(context.lower().replace(' ', '_'))
        
        return metadata
    
    def get_today_tasks(self) -> List[Dict]:
        """Get today's task checklist."""
        tasks = [
            {'task': 'Morning site inspection', 'completed': False, 'priority': 'high'},
            {'task': 'Document new finds', 'completed': False, 'priority': 'high'},
            {'task': 'Update field notes', 'completed': False, 'priority': 'medium'},
            {'task': 'Photo documentation', 'completed': False, 'priority': 'medium'},
            {'task': 'Resource inventory check', 'completed': False, 'priority': 'low'},
            {'task': 'Team check-in', 'completed': False, 'priority': 'high'},
            {'task': 'End of day summary', 'completed': False, 'priority': 'medium'},
        ]
        
        return tasks
    
    def suggest_equipment(self, weather: Optional[Dict] = None,
                         tasks: Optional[List[str]] = None) -> List[str]:
        """Suggest equipment based on weather and planned tasks."""
        equipment = []
        
        if weather:
            if weather.get('temperature', 20) < 10:
                equipment.append('Warm clothing')
            if weather.get('rain_probability', 0) > 0.3:
                equipment.append('Rain gear')
                equipment.append('Waterproof covers for equipment')
            if weather.get('sunny', False):
                equipment.append('Sunscreen')
                equipment.append('Hat')
        
        if tasks:
            if any('excavation' in t.lower() for t in tasks):
                equipment.extend(['Trowels', 'Brushes', 'Sieving equipment'])
            if any('survey' in t.lower() for t in tasks):
                equipment.extend(['GPS', 'Compass', 'Field forms'])
            if any('photo' in t.lower() for t in tasks):
                equipment.extend(['Camera', 'Scale bars', 'Photo log'])
        
        # Always essential
        equipment.extend(['First aid kit', 'Water', 'Field notebook'])
        
        return list(set(equipment))  # Remove duplicates

