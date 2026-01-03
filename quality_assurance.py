"""
Quality Assurance Module
Data completeness checking, consistency validation, and methodology validation
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityAssurance:
    """Performs quality checks on archaeological data."""
    
    def __init__(self):
        self.required_fields = self._get_required_fields()
        self.best_practices = self._get_best_practices()
    
    def _get_required_fields(self) -> Dict[str, List[str]]:
        """Define required fields for different record types."""
        return {
            'site': ['site_name', 'latitude', 'longitude', 'site_type'],
            'artifact': ['artifact_id', 'material', 'context', 'date_recorded'],
            'context': ['context_id', 'trench', 'locus', 'description'],
            'photo': ['photo_id', 'date_taken', 'file_path'],
            'field_note': ['note_id', 'date', 'content'],
        }
    
    def _get_best_practices(self) -> Dict:
        """Get best practices guidelines."""
        return {
            'site_documentation': [
                'GPS coordinates recorded',
                'Site description provided',
                'Photos taken from multiple angles',
                'Site plan or sketch created',
            ],
            'artifact_recording': [
                'Unique identifier assigned',
                'Material type recorded',
                'Context information documented',
                'Measurements taken',
                'Photos with scale included',
            ],
            'stratigraphy': [
                'Harris matrix created',
                'Layer descriptions detailed',
                'Relationships documented',
                'Photos of sections taken',
            ],
            'photography': [
                'Scale included in photos',
                'Multiple angles captured',
                'Metadata recorded',
                'Lighting appropriate',
            ]
        }
    
    def check_data_completeness(self, record_type: str, records: List[Dict]) -> Dict:
        """Check data completeness for a set of records."""
        required = self.required_fields.get(record_type, [])
        
        if not records:
            return {
                'total_records': 0,
                'complete_records': 0,
                'incomplete_records': 0,
                'completeness_percentage': 0.0,
                'missing_fields': {},
                'issues': ['No records provided']
            }
        
        complete_count = 0
        incomplete_records = []
        missing_fields = {field: 0 for field in required}
        
        for record in records:
            record_missing = []
            for field in required:
                if field not in record or not record[field]:
                    missing_fields[field] += 1
                    record_missing.append(field)
            
            if not record_missing:
                complete_count += 1
            else:
                incomplete_records.append({
                    'record_id': record.get('id', 'unknown'),
                    'missing_fields': record_missing
                })
        
        completeness = (complete_count / len(records)) * 100 if records else 0
        
        return {
            'total_records': len(records),
            'complete_records': complete_count,
            'incomplete_records': len(incomplete_records),
            'completeness_percentage': round(completeness, 2),
            'missing_fields': missing_fields,
            'incomplete_record_details': incomplete_records,
            'issues': self._generate_completeness_issues(missing_fields, required)
        }
    
    def _generate_completeness_issues(self, missing_fields: Dict, required: List[str]) -> List[str]:
        """Generate human-readable issues from missing fields."""
        issues = []
        for field, count in missing_fields.items():
            if count > 0:
                issues.append(f"{count} record(s) missing '{field}' field")
        return issues
    
    def validate_consistency(self, records: List[Dict], record_type: str) -> Dict:
        """Validate consistency across records."""
        issues = []
        warnings = []
        
        if record_type == 'site':
            # Check coordinate format
            for record in records:
                lat = record.get('latitude')
                lon = record.get('longitude')
                if lat is not None:
                    if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
                        issues.append(f"Site {record.get('site_name', 'unknown')}: Invalid latitude {lat}")
                if lon is not None:
                    if not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
                        issues.append(f"Site {record.get('site_name', 'unknown')}: Invalid longitude {lon}")
            
            # Check for duplicate site names
            site_names = [r.get('site_name') for r in records if r.get('site_name')]
            duplicates = [name for name in set(site_names) if site_names.count(name) > 1]
            if duplicates:
                warnings.append(f"Duplicate site names found: {', '.join(duplicates)}")
        
        elif record_type == 'artifact':
            # Check material types are consistent
            materials = set(r.get('material', '').lower() for r in records if r.get('material'))
            # Could check against standard list
            
            # Check dates are reasonable
            for record in records:
                date = record.get('date_recorded')
                if date:
                    try:
                        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        if date_obj > datetime.now():
                            warnings.append(f"Artifact {record.get('artifact_id', 'unknown')}: Future date recorded")
                    except:
                        warnings.append(f"Artifact {record.get('artifact_id', 'unknown')}: Invalid date format")
        
        return {
            'consistency_errors': issues,
            'warnings': warnings,
            'total_issues': len(issues) + len(warnings),
            'is_consistent': len(issues) == 0
        }
    
    def check_against_best_practices(self, record_type: str, records: List[Dict]) -> Dict:
        """Check records against best practices."""
        practices = self.best_practices.get(record_type, [])
        
        if not practices:
            return {
                'applicable_practices': [],
                'compliance_score': 100.0,
                'recommendations': []
            }
        
        compliance = {}
        for practice in practices:
            compliance[practice] = False  # Simplified - would need actual checking
        
        # Generate recommendations
        recommendations = []
        for practice, met in compliance.items():
            if not met:
                recommendations.append(f"Consider: {practice}")
        
        compliance_score = (sum(compliance.values()) / len(practices) * 100) if practices else 100
        
        return {
            'applicable_practices': practices,
            'compliance_score': round(compliance_score, 2),
            'recommendations': recommendations
        }
    
    def generate_quality_report(self, project_data: Dict) -> Dict:
        """Generate comprehensive quality report for a project."""
        report = {
            'report_date': datetime.now().isoformat(),
            'sites': {},
            'artifacts': {},
            'overall_score': 0.0,
            'recommendations': []
        }
        
        # Check sites
        sites = project_data.get('sites', [])
        if sites:
            report['sites'] = {
                'completeness': self.check_data_completeness('site', sites),
                'consistency': self.validate_consistency(sites, 'site'),
                'best_practices': self.check_against_best_practices('site_documentation', sites)
            }
        
        # Check artifacts
        artifacts = project_data.get('artifacts', [])
        if artifacts:
            report['artifacts'] = {
                'completeness': self.check_data_completeness('artifact', artifacts),
                'consistency': self.validate_consistency(artifacts, 'artifact'),
                'best_practices': self.check_against_best_practices('artifact_recording', artifacts)
            }
        
        # Calculate overall score
        scores = []
        if sites:
            scores.append(report['sites']['completeness']['completeness_percentage'])
            scores.append(report['sites']['best_practices']['compliance_score'])
        if artifacts:
            scores.append(report['artifacts']['completeness']['completeness_percentage'])
            scores.append(report['artifacts']['best_practices']['compliance_score'])
        
        report['overall_score'] = round(sum(scores) / len(scores), 2) if scores else 0.0
        
        # Generate recommendations
        all_recommendations = []
        if sites:
            all_recommendations.extend(report['sites']['completeness'].get('issues', []))
            all_recommendations.extend(report['sites']['best_practices'].get('recommendations', []))
        if artifacts:
            all_recommendations.extend(report['artifacts']['completeness'].get('issues', []))
            all_recommendations.extend(report['artifacts']['best_practices'].get('recommendations', []))
        
        report['recommendations'] = list(set(all_recommendations))  # Remove duplicates
        
        return report
    
    def get_missing_documentation_checklist(self, project_data: Dict) -> List[Dict]:
        """Get checklist of missing documentation."""
        checklist = []
        
        sites = project_data.get('sites', [])
        for site in sites:
            site_id = site.get('site_name', 'Unknown')
            
            # Check photos
            if not site.get('photos') or len(site.get('photos', [])) == 0:
                checklist.append({
                    'type': 'missing_photos',
                    'item': f"Site: {site_id}",
                    'priority': 'high',
                    'message': f'Missing photos for site {site_id}'
                })
            
            # Check description
            if not site.get('description'):
                checklist.append({
                    'type': 'missing_description',
                    'item': f"Site: {site_id}",
                    'priority': 'medium',
                    'message': f'Missing description for site {site_id}'
                })
        
        artifacts = project_data.get('artifacts', [])
        for artifact in artifacts:
            artifact_id = artifact.get('artifact_id', 'Unknown')
            
            if not artifact.get('photos') or len(artifact.get('photos', [])) == 0:
                checklist.append({
                    'type': 'missing_photos',
                    'item': f"Artifact: {artifact_id}",
                    'priority': 'high',
                    'message': f'Missing photos for artifact {artifact_id}'
                })
            
            if not artifact.get('measurements'):
                checklist.append({
                    'type': 'missing_measurements',
                    'item': f"Artifact: {artifact_id}",
                    'priority': 'medium',
                    'message': f'Missing measurements for artifact {artifact_id}'
                })
        
        return checklist

