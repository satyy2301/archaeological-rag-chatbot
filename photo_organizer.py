"""
Dig Photo Organizer Module
Auto-organizes archaeological dig photos by trench/locus, artifact types, stratigraphy, date, etc.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PIL import Image
from PIL.ExifTags import TAGS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARTIFACT_KEYWORDS = {
    'pottery': ['pottery', 'pot', 'sherd', 'ceramic', 'vessel', 'amphora'],
    'metal': ['metal', 'coin', 'bronze', 'iron', 'copper', 'token', 'medallion'],
    'stone': ['stone', 'lithic', 'tool', 'flint'],
    'bone': ['bone', 'skeleton', 'human', 'animal'],
    'glass': ['glass', 'bead'],
    'organic': ['wood', 'textile', 'organic'],
}


class PhotoOrganizer:
    """Organizes archaeological dig photos with automatic categorization and metadata extraction."""

    def __init__(self, photo_directory: str, analyze_images: bool = True):
        self.photo_directory = Path(photo_directory)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.heic'}
        self.analyze_images = analyze_images
        self.photos = []
        self.last_ocr_backend: Optional[str] = None

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
        """Extract metadata from photo file, filename, and image content."""
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
            'context_id': None,
            'site_id': None,
            'excavation_unit': None,
            'scene_type': None,
            'location': None,
            'notes': None,
            'dimensions': None,
            'metadata_sources': [],
            'detected_labels': [],
            'ocr_backend': None,
        }

        img = None
        try:
            img = Image.open(file_path)
            metadata['dimensions'] = img.size
            exifdata = img.getexif()
            if exifdata:
                for tag_id, value in exifdata.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ('DateTime', 'DateTimeOriginal'):
                        try:
                            metadata['date_taken'] = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        except (ValueError, TypeError):
                            pass
        except Exception as e:
            logger.debug(f"Could not extract EXIF from {file_path}: {e}")

        filename_data = self._parse_filename(file_path.name)
        self._merge_metadata(metadata, filename_data, source='filename')

        if self.analyze_images and img is not None:
            try:
                image_data = self._extract_image_metadata(img)
                self._merge_metadata(metadata, image_data, source=image_data.get('primary_source', 'visual'))
                if image_data.get('ocr_backend'):
                    metadata['ocr_backend'] = image_data['ocr_backend']
                    self.last_ocr_backend = image_data['ocr_backend']
            except Exception as e:
                logger.warning(f"Image analysis failed for {file_path}: {e}")

        if img is not None:
            img.close()

        return metadata

    def _merge_metadata(self, metadata: Dict, new_data: Dict, source: str) -> None:
        """Fill empty metadata fields from a new source without overwriting existing values."""
        field_map = (
            'trench', 'locus', 'artifact_type', 'stratigraphy_layer', 'context_id',
            'site_id', 'excavation_unit', 'scene_type', 'location', 'notes', 'date_from_filename',
        )
        applied = False
        for field in field_map:
            value = new_data.get(field)
            if value and not metadata.get(field):
                metadata[field] = value
                applied = True

        if applied and source not in metadata['metadata_sources']:
            metadata['metadata_sources'].append(source)

        for label in new_data.get('detected_labels', []):
            if label not in metadata['detected_labels']:
                metadata['detected_labels'].append(label)

    def _extract_image_metadata(self, image: Image.Image) -> Dict:
        """Extract trench/locus/artifact metadata from image content via OCR and heuristics."""
        from image_analyzer import enhance_retinex, hough_coin_detection, run_ocr

        enhanced = enhance_retinex(image)
        ocr_payload = run_ocr(enhanced, script_profile='latin')
        ocr_text = self._collect_ocr_text(ocr_payload.get('regions', []))
        parsed = self._parse_field_text(ocr_text)

        coin_result = hough_coin_detection(image)
        scene = self._classify_scene(image, {
            'ocr_text': ocr_text,
            'circles': coin_result.get('circles') or [],
            'parsed': parsed,
        })

        result = {**parsed, **scene}
        result['ocr_backend'] = ocr_payload.get('backend', 'unknown')
        result['detected_labels'] = list(result.get('detected_labels', []))

        if ocr_text.strip():
            result['primary_source'] = 'ocr' if ocr_payload.get('backend') == 'easyocr' else 'visual'
            snippet = ocr_text[:80].replace('\n', ' ')
            result['detected_labels'].append(f'OCR: {snippet}')
        else:
            result['primary_source'] = 'visual'

        if parsed.get('trench'):
            result['detected_labels'].append(f"Trench {parsed['trench']}")
        if parsed.get('locus'):
            result['detected_labels'].append(f"Locus {parsed['locus']}")
        if parsed.get('artifact_type'):
            result['detected_labels'].append(f"Artifact: {parsed['artifact_type']}")
        if parsed.get('stratigraphy_layer'):
            result['detected_labels'].append(f"Layer {parsed['stratigraphy_layer']}")
        if parsed.get('context_id'):
            result['detected_labels'].append(f"Context {parsed['context_id']}")
        if scene.get('scene_type'):
            result['detected_labels'].append(f"Scene: {scene['scene_type']}")

        return result

    def _collect_ocr_text(self, regions: List[Dict]) -> str:
        """Combine OCR region text into one string for field parsing."""
        parts = []
        for item in regions:
            text = (item.get('text') or '').strip()
            if text and float(item.get('confidence', 0.0)) >= 0.15:
                parts.append(text)
        return ' '.join(parts)

    def _parse_field_text(self, full_text: str) -> Dict:
        """Parse archaeological field labels from OCR or visible text."""
        parsed: Dict = {
            'trench': None,
            'locus': None,
            'artifact_type': None,
            'stratigraphy_layer': None,
            'context_id': None,
            'site_id': None,
            'excavation_unit': None,
            'detected_labels': [],
        }
        if not full_text.strip():
            return parsed

        text = full_text.upper().replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text)

        trench_match = re.search(
            r'\bTRENCH\s*[:#]?\s*(\d+)\b|\bT[-\s]?(\d+)\b',
            text,
            re.IGNORECASE,
        )
        if trench_match:
            parsed['trench'] = trench_match.group(1) or trench_match.group(2)

        locus_match = re.search(
            r'\bLOCUS\s*[:#]?\s*(\d+)\b|\bLOC[-\s]?(\d+)\b',
            text,
            re.IGNORECASE,
        )
        if locus_match:
            parsed['locus'] = locus_match.group(1) or locus_match.group(2)

        context_match = re.search(
            r'\bCONTEXT\s*[:#]?\s*\[?(\d+)\]?',
            text,
            re.IGNORECASE,
        )
        if context_match:
            parsed['context_id'] = context_match.group(1)
            if not parsed['stratigraphy_layer']:
                parsed['stratigraphy_layer'] = context_match.group(1)

        layer_match = re.search(
            r'\b(?:LAYER|STRAT|STRATUM|STRATIGRAPHY)\s*[:#]?\s*(\d+)\b',
            text,
            re.IGNORECASE,
        )
        if layer_match:
            parsed['stratigraphy_layer'] = layer_match.group(1)

        object_match = re.search(
            r'\bOBJECT\s*[:#]?\s*([A-Z][A-Z0-9 /-]{1,40})',
            text,
            re.IGNORECASE,
        )
        if object_match:
            object_value = object_match.group(1).strip()
            artifact = self._normalize_artifact_type(object_value)
            if artifact:
                parsed['artifact_type'] = artifact
                parsed['detected_labels'].append(f"Object: {object_value.title()}")

        material_match = re.search(
            r'\bMATERIAL\s*[:#]?\s*([A-Z][A-Z0-9 /-]{1,30})',
            text,
            re.IGNORECASE,
        )
        if material_match and not parsed.get('artifact_type'):
            material_value = material_match.group(1).strip()
            artifact = self._normalize_artifact_type(material_value)
            if artifact:
                parsed['artifact_type'] = artifact
                parsed['detected_labels'].append(f"Material: {material_value.title()}")

        site_match = re.search(
            r'\bSITE\s*ID\s*[:#]?\s*([A-Z0-9-]+)',
            text,
            re.IGNORECASE,
        )
        if site_match:
            parsed['site_id'] = site_match.group(1)

        unit_match = re.search(
            r'\bEXCAVATION\s+UNIT\s*[:#]?\s*([A-Z0-9-]+)',
            text,
            re.IGNORECASE,
        )
        if unit_match:
            parsed['excavation_unit'] = unit_match.group(1)

        if not parsed.get('artifact_type'):
            artifact = self._normalize_artifact_type(text)
            if artifact:
                parsed['artifact_type'] = artifact

        return parsed

    def _normalize_artifact_type(self, text: str) -> Optional[str]:
        """Map free text to standard artifact type buckets."""
        text_lower = text.lower()
        for artifact_type, keywords in ARTIFACT_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return artifact_type
        return None

    def _classify_scene(self, image: Image.Image, hints: Dict) -> Dict:
        """Classify photo scene using lightweight visual heuristics."""
        import numpy as np
        from image_analyzer import pil_to_cv

        width, height = image.size
        aspect = width / height if height else 1.0
        parsed = hints.get('parsed') or {}
        circles = hints.get('circles') or []
        ocr_text = (hints.get('ocr_text') or '').lower()

        result: Dict = {
            'scene_type': None,
            'artifact_type': None,
            'stratigraphy_layer': None,
            'detected_labels': [],
        }

        cv_img = pil_to_cv(image.convert('RGB'))
        gray = cv_img.mean(axis=2)
        avg_brightness = float(gray.mean())
        r_mean = float(cv_img[:, :, 2].mean())
        g_mean = float(cv_img[:, :, 1].mean())
        b_mean = float(cv_img[:, :, 0].mean())

        has_green_patina = g_mean > r_mean + 15 and g_mean > b_mean + 10
        has_warm_earth = r_mean > b_mean + 20 and avg_brightness < 180

        if circles and (has_green_patina or 'coin' in ocr_text or 'bronze' in ocr_text):
            result['scene_type'] = 'artifact_closeup'
            if not parsed.get('artifact_type'):
                result['artifact_type'] = 'metal'
            result['detected_labels'].append('Round metal object detected')

        elif any(word in ocr_text for word in ('pottery', 'sherd', 'ceramic', 'vessel')):
            result['scene_type'] = 'excavation'
            result['artifact_type'] = 'pottery'
            result['detected_labels'].append('Pottery-related scene')

        elif self._has_horizontal_banding(cv_img):
            result['scene_type'] = 'stratigraphy'
            result['detected_labels'].append('Horizontal soil layers visible')
            if not parsed.get('stratigraphy_layer'):
                result['stratigraphy_layer'] = parsed.get('context_id')

        elif aspect > 1.4 and width > 900:
            result['scene_type'] = 'site_overview'
            result['detected_labels'].append('Wide excavation overview')

        elif has_warm_earth and height > width:
            result['scene_type'] = 'excavation'
            if not parsed.get('artifact_type'):
                result['artifact_type'] = 'pottery'
            result['detected_labels'].append('In-situ excavation find')

        elif 'field record' in ocr_text or 'excavation unit' in ocr_text:
            result['scene_type'] = 'artifact_closeup'
            result['detected_labels'].append('Field documentation form visible')

        return result

    def _has_horizontal_banding(self, cv_img) -> bool:
        """Detect strong horizontal stratigraphy bands in trench-wall photos."""
        import cv2

        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        row_stds = gray.std(axis=1)
        if len(row_stds) < 20:
            return False

        peaks = 0
        threshold = float(row_stds.mean() + row_stds.std() * 0.5)
        for idx in range(1, len(row_stds) - 1):
            if row_stds[idx] > threshold and row_stds[idx] > row_stds[idx - 1] and row_stds[idx] > row_stds[idx + 1]:
                peaks += 1
        return peaks >= 4

    def _parse_filename(self, filename: str) -> Dict:
        """Parse archaeological metadata from filename patterns."""
        parsed = {
            'trench': None,
            'locus': None,
            'artifact_type': None,
            'stratigraphy_layer': None,
            'date_from_filename': None,
            'detected_labels': [],
        }

        trench_match = re.search(
            r'(?:^|[_\-.])T(?:rench)?[-_]?(\d+)|\bTRENCH[-_\s]?(\d+)',
            filename,
            re.IGNORECASE,
        )
        if trench_match:
            parsed['trench'] = trench_match.group(1) or trench_match.group(2)

        locus_match = re.search(
            r'(?:^|[_\-.])L(?:ocus)?[-_]?(\d+)|\bLOCUS[-_\s]?(\d+)',
            filename,
            re.IGNORECASE,
        )
        if locus_match:
            parsed['locus'] = locus_match.group(1) or locus_match.group(2)

        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{4})(\d{2})(\d{2})',
            r'(\d{2})-(\d{2})-(\d{4})',
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, filename)
            if date_match:
                try:
                    if len(date_match.group(1)) == 4:
                        year, month, day = date_match.groups()
                        parsed['date_from_filename'] = datetime(int(year), int(month), int(day))
                    else:
                        day, month, year = date_match.groups()
                        parsed['date_from_filename'] = datetime(int(year), int(month), int(day))
                    break
                except (ValueError, TypeError):
                    pass

        artifact = self._normalize_artifact_type(filename)
        if artifact:
            parsed['artifact_type'] = artifact

        strat_match = re.search(r'\b(?:Layer|Strat|Stratum)(\d+)\b', filename, re.IGNORECASE)
        if strat_match:
            parsed['stratigraphy_layer'] = strat_match.group(1)

        return parsed

    def _artifact_category(self, photo: Dict) -> str:
        """Resolve artifact grouping with scene_type fallback."""
        if photo.get('artifact_type'):
            return photo['artifact_type']
        if photo.get('scene_type'):
            return photo['scene_type']
        return 'Unknown'

    def _stratigraphy_category(self, photo: Dict) -> str:
        """Resolve stratigraphy grouping with context_id fallback."""
        if photo.get('stratigraphy_layer'):
            return str(photo['stratigraphy_layer'])
        if photo.get('context_id'):
            return f"Context {photo['context_id']}"
        return 'Unknown'

    def organize_by_trench(self) -> Dict[str, List[Dict]]:
        """Organize photos by trench number."""
        organized: Dict[str, List[Dict]] = {}
        for photo in self.photos:
            trench = photo.get('trench') or 'Unknown'
            organized.setdefault(trench, []).append(photo)
        return organized

    def organize_by_locus(self) -> Dict[str, List[Dict]]:
        """Organize photos by locus number."""
        organized: Dict[str, List[Dict]] = {}
        for photo in self.photos:
            locus = photo.get('locus') or 'Unknown'
            organized.setdefault(locus, []).append(photo)
        return organized

    def organize_by_artifact_type(self) -> Dict[str, List[Dict]]:
        """Organize photos by artifact type or scene fallback."""
        organized: Dict[str, List[Dict]] = {}
        for photo in self.photos:
            artifact_type = self._artifact_category(photo)
            organized.setdefault(artifact_type, []).append(photo)
        return organized

    def organize_by_stratigraphy(self) -> Dict[str, List[Dict]]:
        """Organize photos by stratigraphy layer or context fallback."""
        organized: Dict[str, List[Dict]] = {}
        for photo in self.photos:
            layer = self._stratigraphy_category(photo)
            organized.setdefault(layer, []).append(photo)
        return organized

    def organize_by_date(self) -> Dict[str, List[Dict]]:
        """Organize photos by date taken."""
        organized: Dict[str, List[Dict]] = {}
        for photo in self.photos:
            date = photo.get('date_taken') or photo.get('date_from_filename') or photo.get('date_modified')
            if date:
                date_key = date.strftime('%Y-%m-%d')
                organized.setdefault(date_key, []).append(photo)
            else:
                organized.setdefault('No Date', []).append(photo)
        return organized

    def find_duplicates(self, similarity_threshold: float = 0.95) -> List[List[Dict]]:
        """Find duplicate or near-duplicate photos based on file size and dimensions."""
        duplicates = []
        seen = {}

        for photo in self.photos:
            key = (photo.get('file_size'), photo.get('dimensions'))
            if key in seen:
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

        by_trench = self.organize_by_trench()
        report_lines.append("### By Trench")
        for trench, photos in sorted(by_trench.items()):
            report_lines.append(f"- Trench {trench}: {len(photos)} photos")

        by_locus = self.organize_by_locus()
        report_lines.append("\n### By Locus")
        for locus, photos in sorted(by_locus.items()):
            report_lines.append(f"- Locus {locus}: {len(photos)} photos")

        by_artifact = self.organize_by_artifact_type()
        report_lines.append("\n### By Artifact Type / Scene")
        for artifact_type, photos in sorted(by_artifact.items()):
            report_lines.append(f"- {artifact_type}: {len(photos)} photos")

        by_strat = self.organize_by_stratigraphy()
        report_lines.append("\n### By Stratigraphy Layer")
        for layer, photos in sorted(by_strat.items()):
            report_lines.append(f"- {layer}: {len(photos)} photos")

        by_scene = self._count_by_field('scene_type')
        if by_scene:
            report_lines.append("\n### By Scene Type")
            for scene, count in sorted(by_scene.items()):
                report_lines.append(f"- {scene}: {count} photos")

        by_date = self.organize_by_date()
        report_lines.append("\n### By Date")
        for date_key, photos in sorted(by_date.items()):
            report_lines.append(f"- {date_key}: {len(photos)} photos")

        detection_counts = self._detection_source_counts()
        report_lines.append("\n### Detection Methods")
        for source, count in sorted(detection_counts.items()):
            report_lines.append(f"- {source}: {count} photos")

        duplicates = self.find_duplicates()
        if duplicates:
            report_lines.append("\n### Potential Duplicates")
            report_lines.append(f"Found {len(duplicates)} potential duplicate groups")

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
            'by_scene_type': self._count_by_field('scene_type'),
            'detection_sources': self._detection_source_counts(),
            'ocr_backend': self.last_ocr_backend,
            'date_range': self._get_date_range(),
            'duplicate_count': len(self.find_duplicates()),
            'missing_documentation': {
                'no_trench': len([p for p in self.photos if not p.get('trench')]),
                'no_locus': len([p for p in self.photos if not p.get('locus')]),
                'no_date': len([p for p in self.photos if not (p.get('date_taken') or p.get('date_from_filename'))]),
            },
        }

    def _count_by_field(self, field: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for photo in self.photos:
            value = photo.get(field)
            if value:
                key = str(value)
                counts[key] = counts.get(key, 0) + 1
        return counts

    def _detection_source_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for photo in self.photos:
            for source in photo.get('metadata_sources', []):
                counts[source] = counts.get(source, 0) + 1
        return counts

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

    @staticmethod
    def format_photo_chips(photo: Dict) -> List[str]:
        """Build short metadata chips for UI display."""
        chips = []
        if photo.get('trench'):
            chips.append(f"Trench {photo['trench']}")
        if photo.get('locus'):
            chips.append(f"Locus {photo['locus']}")
        if photo.get('artifact_type'):
            chips.append(photo['artifact_type'].title())
        elif photo.get('scene_type'):
            chips.append(photo['scene_type'].replace('_', ' ').title())
        if photo.get('stratigraphy_layer'):
            chips.append(f"Layer {photo['stratigraphy_layer']}")
        if photo.get('context_id'):
            chips.append(f"Context {photo['context_id']}")
        sources = photo.get('metadata_sources') or []
        if sources:
            chips.append(f"via {', '.join(sources)}")
        return chips
