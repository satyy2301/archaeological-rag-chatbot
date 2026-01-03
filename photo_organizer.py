"""
Dig Photo Organizer Module
Auto-organizes archaeological dig photos by trench/locus, artifact types, stratigraphy, date, etc.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PIL import Image
from PIL.ExifTags import TAGS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhotoOrganizer:
    """Organizes archaeological dig photos with automatic categorization and metadata extraction."""
    
    def __init__(self, photo_directory: str):
        self.photo_directory = Path(photo_directory)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic'}
        self.photos = []
        
    def scan_directory(self) -> List[Dict]:
        """Scan directory for photos and extract metadata."""
        if not self.photo_directory.exists():
            logger.error(f"Directory not found: {self.photo_directory}")
            return []
            
        photos = []
        for file_path in self.photo_directory.rglob('*'):
            if file_path.suffix.lower() in self.supported_formats:
                try:
                    metadata = self._extract_metadata(file_path)
                    photos.append(metadata)
                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {e}")
                    
        self.photos = photos
        return photos
    
    def _extract_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from photo file."""
        metadata = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'date_taken': None,
            'date_modified': datetime.fromtimestamp(file_path.stat().st_mtime),
            'trench': None,
            'locus': None,
            'artifact_type': None,
            'stratigraphy_layer': None,
            'location': None,
            'notes': None,
            'dimensions': None,
        }
        
        # Extract EXIF data
        try:
            with Image.open(file_path) as img:
                metadata['dimensions'] = img.size
                exifdata = img.getexif()
                if exifdata:
                    for tag_id, value in exifdata.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'DateTime':
                            try:
                                metadata['date_taken'] = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                            except:
                                pass
                        elif tag == 'DateTimeOriginal':
                            try:
                                metadata['date_taken'] = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                            except:
                                pass
        except Exception as e:
            logger.debug(f"Could not extract EXIF from {file_path}: {e}")
        
        # Extract metadata from filename
        metadata.update(self._parse_filename(file_path.name))
        
        return metadata
    
    def _parse_filename(self, filename: str) -> Dict:
        """Parse archaeological metadata from filename patterns."""
        parsed = {
            'trench': None,
            'locus': None,
            'artifact_type': None,
            'stratigraphy_layer': None,
            'date_from_filename': None,
        }
        
        # Common patterns:
        # Trench patterns: T1, T-01, TR01, Trench_1
        trench_match = re.search(r'\bT(?:rench[-_]?)?(\d+)\b', filename, re.IGNORECASE)
        if trench_match:
            parsed['trench'] = trench_match.group(1)
        
        # Locus patterns: L1, L-01, Loc_1, Locus_01
        locus_match = re.search(r'\bL(?:ocus[-_]?)?(\d+)\b', filename, re.IGNORECASE)
        if locus_match:
            parsed['locus'] = locus_match.group(1)
        
        # Date patterns: YYYY-MM-DD, YYYYMMDD, DD-MM-YYYY
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{4})(\d{2})(\d{2})',
            r'(\d{2})-(\d{2})-(\d{4})',
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, filename)
            if date_match:
                try:
                    if len(date_match.group(1)) == 4:  # YYYY-MM-DD or YYYYMMDD
                        year, month, day = date_match.groups()
                        parsed['date_from_filename'] = datetime(int(year), int(month), int(day))
                    else:  # DD-MM-YYYY
                        day, month, year = date_match.groups()
                        parsed['date_from_filename'] = datetime(int(year), int(month), int(day))
                    break
                except:
                    pass
        
        # Artifact type keywords
        artifact_keywords = {
            'pottery': ['pottery', 'pot', 'sherd', 'ceramic'],
            'metal': ['metal', 'coin', 'bronze', 'iron', 'copper'],
            'stone': ['stone', 'lithic', 'tool', 'flint'],
            'bone': ['bone', 'skeleton', 'human', 'animal'],
            'glass': ['glass', 'bead'],
            'organic': ['wood', 'textile', 'organic'],
        }
        filename_lower = filename.lower()
        for artifact_type, keywords in artifact_keywords.items():
            if any(keyword in filename_lower for keyword in keywords):
                parsed['artifact_type'] = artifact_type
                break
        
        # Stratigraphy patterns: Layer, Strat, L, Stratum
        strat_match = re.search(r'\b(?:Layer|Strat|Stratum|L\.?)(\d+)\b', filename, re.IGNORECASE)
        if strat_match:
            parsed['stratigraphy_layer'] = strat_match.group(1)
        
        return parsed
    
    def organize_by_trench(self) -> Dict[str, List[Dict]]:
        """Organize photos by trench number."""
        organized = {}
        for photo in self.photos:
            trench = photo.get('trench') or 'Unknown'
            if trench not in organized:
                organized[trench] = []
            organized[trench].append(photo)
        return organized
    
    def organize_by_locus(self) -> Dict[str, List[Dict]]:
        """Organize photos by locus number."""
        organized = {}
        for photo in self.photos:
            locus = photo.get('locus') or 'Unknown'
            if locus not in organized:
                organized[locus] = []
            organized[locus].append(photo)
        return organized
    
    def organize_by_artifact_type(self) -> Dict[str, List[Dict]]:
        """Organize photos by artifact type."""
        organized = {}
        for photo in self.photos:
            artifact_type = photo.get('artifact_type') or 'Unknown'
            if artifact_type not in organized:
                organized[artifact_type] = []
            organized[artifact_type].append(photo)
        return organized
    
    def organize_by_stratigraphy(self) -> Dict[str, List[Dict]]:
        """Organize photos by stratigraphy layer."""
        organized = {}
        for photo in self.photos:
            layer = photo.get('stratigraphy_layer') or 'Unknown'
            if layer not in organized:
                organized[layer] = []
            organized[layer].append(photo)
        return organized
    
    def organize_by_date(self) -> Dict[str, List[Dict]]:
        """Organize photos by date taken."""
        organized = {}
        for photo in self.photos:
            date = photo.get('date_taken') or photo.get('date_from_filename') or photo.get('date_modified')
            if date:
                date_key = date.strftime('%Y-%m-%d')
                if date_key not in organized:
                    organized[date_key] = []
                organized[date_key].append(photo)
            else:
                if 'No Date' not in organized:
                    organized['No Date'] = []
                organized['No Date'].append(photo)
        return organized
    
    def find_duplicates(self, similarity_threshold: float = 0.95) -> List[List[Dict]]:
        """Find duplicate or near-duplicate photos based on file size and dimensions."""
        # Simple duplicate detection based on file size and dimensions
        # For production, consider using perceptual hashing (e.g., imagehash library)
        duplicates = []
        seen = {}
        
        for photo in self.photos:
            key = (photo.get('file_size'), photo.get('dimensions'))
            if key in seen:
                # Check if this is part of an existing duplicate group
                found_group = False
                for group in duplicates:
                    if seen[key] in group:
                        group.append(photo)
                        found_group = True
                        break
                if not found_group:
                    duplicates.append([seen[key], photo])
            else:
                seen[key] = photo
        
        return duplicates
    
    def generate_field_report(self, output_path: Optional[str] = None) -> str:
        """Generate a field report from photo metadata."""
        report_lines = [
            "# Archaeological Dig Photo Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Photos: {len(self.photos)}",
            "",
            "## Summary by Category",
            "",
        ]
        
        # Trench summary
        by_trench = self.organize_by_trench()
        report_lines.append("### By Trench")
        for trench, photos in sorted(by_trench.items()):
            report_lines.append(f"- Trench {trench}: {len(photos)} photos")
        
        # Locus summary
        by_locus = self.organize_by_locus()
        report_lines.append("\n### By Locus")
        for locus, photos in sorted(by_locus.items()):
            report_lines.append(f"- Locus {locus}: {len(photos)} photos")
        
        # Artifact type summary
        by_artifact = self.organize_by_artifact_type()
        report_lines.append("\n### By Artifact Type")
        for artifact_type, photos in sorted(by_artifact.items()):
            report_lines.append(f"- {artifact_type}: {len(photos)} photos")
        
        # Date summary
        by_date = self.organize_by_date()
        report_lines.append("\n### By Date")
        for date_key, photos in sorted(by_date.items()):
            report_lines.append(f"- {date_key}: {len(photos)} photos")
        
        # Duplicates
        duplicates = self.find_duplicates()
        if duplicates:
            report_lines.append("\n### Potential Duplicates")
            report_lines.append(f"Found {len(duplicates)} potential duplicate groups")
        
        # Missing documentation
        report_lines.append("\n### Missing Documentation")
        missing_trench = [p for p in self.photos if not p.get('trench')]
        missing_locus = [p for p in self.photos if not p.get('locus')]
        missing_date = [p for p in self.photos if not (p.get('date_taken') or p.get('date_from_filename'))]
        
        report_lines.append(f"- Photos without trench number: {len(missing_trench)}")
        report_lines.append(f"- Photos without locus number: {len(missing_locus)}")
        report_lines.append(f"- Photos without date: {len(missing_date)}")
        
        report = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report
    
    def get_statistics(self) -> Dict:
        """Get statistics about the photo collection."""
        return {
            'total_photos': len(self.photos),
            'by_trench': {k: len(v) for k, v in self.organize_by_trench().items()},
            'by_locus': {k: len(v) for k, v in self.organize_by_locus().items()},
            'by_artifact_type': {k: len(v) for k, v in self.organize_by_artifact_type().items()},
            'by_stratigraphy': {k: len(v) for k, v in self.organize_by_stratigraphy().items()},
            'date_range': self._get_date_range(),
            'duplicate_count': len(self.find_duplicates()),
            'missing_documentation': {
                'no_trench': len([p for p in self.photos if not p.get('trench')]),
                'no_locus': len([p for p in self.photos if not p.get('locus')]),
                'no_date': len([p for p in self.photos if not (p.get('date_taken') or p.get('date_from_filename'))]),
            }
        }
    
    def _get_date_range(self) -> Optional[Tuple[datetime, datetime]]:
        """Get the date range of all photos."""
        dates = []
        for photo in self.photos:
            date = photo.get('date_taken') or photo.get('date_from_filename')
            if date:
                dates.append(date)
        
        if dates:
            return (min(dates), max(dates))
        return None

