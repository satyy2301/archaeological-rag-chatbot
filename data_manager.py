"""
Data Management Module
Handles project-based organization, version control, export/import, and backups
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataManager:
    """Manages project data, exports, imports, and backups."""
    
    def __init__(self, base_directory: str = "./user_data"):
        self.base_directory = Path(base_directory)
        self.projects_directory = self.base_directory / "projects"
        self.backups_directory = self.base_directory / "backups"
        self.projects_directory.mkdir(parents=True, exist_ok=True)
        self.backups_directory.mkdir(parents=True, exist_ok=True)
    
    def get_project_directory(self, project_id: str) -> Path:
        """Get or create project directory."""
        project_dir = self.projects_directory / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def save_project_data(self, project_id: str, data_type: str, data: Any, 
                         metadata: Optional[Dict] = None) -> bool:
        """Save data to project directory."""
        try:
            project_dir = self.get_project_directory(project_id)
            data_dir = project_dir / data_type
            data_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if data_type == "documents":
                # For documents, data should be file path or content
                if isinstance(data, str) and os.path.exists(data):
                    # Copy file
                    dest = data_dir / f"{timestamp}_{Path(data).name}"
                    shutil.copy2(data, dest)
                    data_path = str(dest)
                else:
                    # Save as text
                    data_path = data_dir / f"{timestamp}_document.txt"
                    with open(data_path, 'w', encoding='utf-8') as f:
                        f.write(str(data))
                    data_path = str(data_path)
            elif data_type == "sites":
                # Save as JSON
                data_path = data_dir / f"{timestamp}_sites.json"
                with open(data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                data_path = str(data_path)
            elif data_type == "artifacts":
                # Save as JSON
                data_path = data_dir / f"{timestamp}_artifacts.json"
                with open(data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                data_path = str(data_path)
            elif data_type == "chat_history":
                # Save as JSON
                data_path = data_dir / f"{timestamp}_chat.json"
                with open(data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                data_path = str(data_path)
            elif data_type == "maps":
                # Save as JSON
                data_path = data_dir / f"{timestamp}_maps.json"
                with open(data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                data_path = str(data_path)
            else:
                # Generic JSON save
                data_path = data_dir / f"{timestamp}_{data_type}.json"
                with open(data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
                data_path = str(data_path)
            
            # Save metadata
            if metadata:
                meta_path = Path(data_path).with_suffix('.meta.json')
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"Saved {data_type} to project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving project data: {e}")
            return False
    
    def load_project_data(self, project_id: str, data_type: str) -> List[Dict]:
        """Load all data of a specific type from project."""
        try:
            project_dir = self.get_project_directory(project_id)
            data_dir = project_dir / data_type
            
            if not data_dir.exists():
                return []
            
            items = []
            for file_path in sorted(data_dir.glob('*')):
                if file_path.suffix == '.json' and not file_path.name.endswith('.meta.json'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            items.append({
                                'data': data,
                                'file_path': str(file_path),
                                'timestamp': file_path.stem.split('_', 2)[:2] if '_' in file_path.stem else None
                            })
                    except Exception as e:
                        logger.warning(f"Error loading {file_path}: {e}")
                elif file_path.is_file() and file_path.suffix != '.json':
                    items.append({
                        'data': str(file_path),
                        'file_path': str(file_path),
                        'timestamp': file_path.stem.split('_', 2)[:2] if '_' in file_path.stem else None
                    })
            
            return items
            
        except Exception as e:
            logger.error(f"Error loading project data: {e}")
            return []
    
    def export_to_csv(self, project_id: str, data_type: str, output_path: str) -> bool:
        """Export project data to CSV."""
        try:
            items = self.load_project_data(project_id, data_type)
            if not items:
                return False
            
            # Convert to DataFrame
            if data_type in ['sites', 'artifacts']:
                data_list = [item['data'] for item in items if isinstance(item['data'], dict)]
                if data_list:
                    df = pd.json_normalize(data_list)
                    df.to_csv(output_path, index=False)
                    return True
            elif data_type == 'maps':
                # Flatten map data
                data_list = []
                for item in items:
                    if isinstance(item['data'], dict):
                        data_list.append(item['data'])
                if data_list:
                    df = pd.json_normalize(data_list)
                    df.to_csv(output_path, index=False)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def export_to_geojson(self, project_id: str, data_type: str, output_path: str) -> bool:
        """Export sites/maps to GeoJSON format."""
        try:
            items = self.load_project_data(project_id, data_type)
            if not items:
                return False
            
            features = []
            for item in items:
                data = item['data']
                if isinstance(data, dict) and 'latitude' in data and 'longitude' in data:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [data['longitude'], data['latitude']]
                        },
                        "properties": {k: v for k, v in data.items() if k not in ['latitude', 'longitude']}
                    }
                    features.append(feature)
            
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to GeoJSON: {e}")
            return False
    
    def import_from_csv(self, project_id: str, data_type: str, csv_path: str) -> bool:
        """Import data from CSV file."""
        try:
            df = pd.read_csv(csv_path)
            data = df.to_dict('records')
            
            metadata = {
                'imported_from': csv_path,
                'import_date': datetime.now().isoformat(),
                'record_count': len(data)
            }
            
            return self.save_project_data(project_id, data_type, data, metadata)
            
        except Exception as e:
            logger.error(f"Error importing from CSV: {e}")
            return False
    
    def import_from_geojson(self, project_id: str, data_type: str, geojson_path: str) -> bool:
        """Import sites from GeoJSON file."""
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson = json.load(f)
            
            sites = []
            for feature in geojson.get('features', []):
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [])
                if len(coords) >= 2:
                    props['longitude'] = coords[0]
                    props['latitude'] = coords[1]
                sites.append(props)
            
            metadata = {
                'imported_from': geojson_path,
                'import_date': datetime.now().isoformat(),
                'record_count': len(sites)
            }
            
            return self.save_project_data(project_id, data_type, sites, metadata)
            
        except Exception as e:
            logger.error(f"Error importing from GeoJSON: {e}")
            return False
    
    def create_backup(self, project_id: str) -> Optional[str]:
        """Create a backup of project data."""
        try:
            project_dir = self.get_project_directory(project_id)
            if not project_dir.exists():
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backups_directory / f"{project_id}_{timestamp}"
            
            shutil.copytree(project_dir, backup_path)
            
            # Save backup metadata
            backup_meta = {
                'project_id': project_id,
                'backup_date': datetime.now().isoformat(),
                'backup_path': str(backup_path)
            }
            meta_file = backup_path / "backup_metadata.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(backup_meta, f, indent=2)
            
            logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, project_id: str, backup_path: str) -> bool:
        """Restore project from backup."""
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                return False
            
            project_dir = self.get_project_directory(project_id)
            
            # Create backup before restore
            self.create_backup(project_id)
            
            # Remove existing project directory
            if project_dir.exists():
                shutil.rmtree(project_dir)
            
            # Copy backup
            shutil.copytree(backup_dir, project_dir)
            
            logger.info(f"Backup restored: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self, project_id: str) -> List[Dict]:
        """List all backups for a project."""
        backups = []
        for backup_dir in self.backups_directory.glob(f"{project_id}_*"):
            if backup_dir.is_dir():
                meta_file = backup_dir / "backup_metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            backups.append(metadata)
                    except:
                        backups.append({
                            'backup_path': str(backup_dir),
                            'backup_date': backup_dir.name.split('_', 1)[1] if '_' in backup_dir.name else 'unknown'
                        })
        return sorted(backups, key=lambda x: x.get('backup_date', ''), reverse=True)
    
    def get_project_statistics(self, project_id: str) -> Dict:
        """Get statistics about project data."""
        stats = {
            'documents': 0,
            'sites': 0,
            'artifacts': 0,
            'maps': 0,
            'chat_sessions': 0,
            'total_size_mb': 0
        }
        
        project_dir = self.get_project_directory(project_id)
        
        for data_type in ['documents', 'sites', 'artifacts', 'maps', 'chat_history']:
            data_dir = project_dir / data_type
            if data_dir.exists():
                count = len(list(data_dir.glob('*')))
                # Count only non-metadata files
                count = len([f for f in data_dir.glob('*') if not f.name.endswith('.meta.json')])
                stats[data_type.replace('_history', '_sessions')] = count
                
                # Calculate size
                for file_path in data_dir.rglob('*'):
                    if file_path.is_file():
                        stats['total_size_mb'] += file_path.stat().st_size / (1024 * 1024)
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats

