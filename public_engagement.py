"""
Public Engagement Module
Story builder, interactive timelines, and educational materials
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PublicEngagement:
    """Creates public-facing content from archaeological data."""
    
    def __init__(self, rag_chain=None):
        self.rag_chain = rag_chain
    
    def build_site_story(self, site_data: Dict, period_info: Optional[Dict] = None) -> str:
        """Build an engaging story about a site for public audiences."""
        story_parts = []
        
        site_name = site_data.get('site_name', 'this archaeological site')
        site_type = site_data.get('site_type', 'site')
        
        # Introduction
        story_parts.append(f"## The Story of {site_name}")
        story_parts.append("")
        
        # Context
        if period_info:
            period = period_info.get('period', 'ancient times')
            culture = period_info.get('culture', 'ancient people')
            story_parts.append(
                f"Over {period_info.get('years_ago', 'thousands')} years ago, {culture} lived at {site_name}. "
                f"This {site_type} tells us about their daily lives, their culture, and their relationship with the landscape."
            )
        else:
            story_parts.append(
                f"{site_name} is an important {site_type} that reveals secrets about the past. "
                "Through careful archaeological investigation, we can piece together the story of the people who lived here."
            )
        
        story_parts.append("")
        
        # Findings
        if site_data.get('key_findings'):
            story_parts.append("### Discoveries")
            story_parts.append("")
            findings = site_data['key_findings']
            if isinstance(findings, list):
                for finding in findings:
                    story_parts.append(f"- {finding}")
            else:
                story_parts.append(findings)
            story_parts.append("")
        
        # Significance
        story_parts.append("### Why This Matters")
        story_parts.append("")
        story_parts.append(
            f"Understanding {site_name} helps us learn about the past and how people have lived in this region. "
            "Each artifact, each structure, each layer of soil tells a story about human history."
        )
        story_parts.append("")
        
        # Preservation message
        story_parts.append("### Protecting Our Heritage")
        story_parts.append("")
        story_parts.append(
            "Archaeological sites are fragile and non-renewable. Once destroyed, the information they contain is lost forever. "
            "By protecting and studying these sites, we preserve our shared heritage for future generations."
        )
        
        return "\n".join(story_parts)
    
    def create_interactive_timeline(self, timeline_data: List[Dict]) -> Dict:
        """Create an interactive timeline from chronological data."""
        timeline = {
            'title': 'Site Timeline',
            'events': []
        }
        
        # Sort by date
        sorted_events = sorted(timeline_data, key=lambda x: self._extract_year(x.get('date', '')))
        
        for event in sorted_events:
            timeline_event = {
                'date': event.get('date', ''),
                'title': event.get('title', event.get('site_name', 'Event')),
                'description': event.get('description', ''),
                'category': event.get('category', 'general')
            }
            timeline['events'].append(timeline_event)
        
        return timeline
    
    def _extract_year(self, date_str: str) -> int:
        """Extract year from date string for sorting."""
        try:
            if isinstance(date_str, str):
                # Try to extract year
                import re
                year_match = re.search(r'\d{4}', date_str)
                if year_match:
                    return int(year_match.group())
            elif isinstance(date_str, (int, float)):
                return int(date_str)
        except:
            pass
        return 0
    
    def generate_educational_materials(self, topic: str, content_data: Dict) -> Dict:
        """Generate educational materials for a topic."""
        materials = {
            'topic': topic,
            'overview': '',
            'key_points': [],
            'activities': [],
            'resources': []
        }
        
        # Generate overview
        if self.rag_chain:
            prompt = f"Create an educational overview about {topic} for general audiences. Keep it engaging and accessible."
            try:
                result = self.rag_chain.query(prompt)
                materials['overview'] = result.get('answer', f"Learn about {topic} through archaeological investigation.")
            except:
                materials['overview'] = f"Learn about {topic} through archaeological investigation."
        else:
            materials['overview'] = f"Learn about {topic} through archaeological investigation."
        
        # Key points
        materials['key_points'] = [
            f"Understanding {topic} helps us learn about the past",
            "Archaeological methods reveal information about ancient lives",
            "Preservation is important for future generations"
        ]
        
        # Suggested activities
        materials['activities'] = [
            f"Visit a local museum to see artifacts related to {topic}",
            "Research how archaeologists study this topic",
            "Create a timeline showing the development of this topic"
        ]
        
        return materials
    
    def create_virtual_tour_structure(self, site_data: Dict, photos: List[Dict]) -> Dict:
        """Create structure for a virtual tour from photos and site data."""
        tour = {
            'site_name': site_data.get('site_name', 'Site Tour'),
            'introduction': site_data.get('description', ''),
            'stops': []
        }
        
        # Organize photos into tour stops
        for idx, photo in enumerate(photos[:10], 1):  # Limit to 10 stops
            stop = {
                'stop_number': idx,
                'title': photo.get('title', f'Stop {idx}'),
                'description': photo.get('description', ''),
                'photo_path': photo.get('path', ''),
                'location': photo.get('location', {})
            }
            tour['stops'].append(stop)
        
        return tour
    
    def generate_press_release_template(self, project_data: Dict) -> str:
        """Generate a press release template."""
        lines = []
        
        lines.append("# Press Release")
        lines.append("")
        lines.append(f"**FOR IMMEDIATE RELEASE**")
        lines.append("")
        lines.append(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")
        lines.append("")
        lines.append(f"## {project_data.get('project_name', 'Archaeological Investigation')}")
        lines.append("")
        lines.append("### Summary")
        lines.append("")
        lines.append(f"[Insert summary of {project_data.get('project_name', 'the investigation')}]")
        lines.append("")
        lines.append("### Key Findings")
        lines.append("")
        sites_count = len(project_data.get('sites', []))
        artifacts_count = len(project_data.get('artifacts', []))
        
        if sites_count > 0:
            lines.append(f"- {sites_count} site(s) documented")
        if artifacts_count > 0:
            lines.append(f"- {artifacts_count} artifact(s) recorded")
        
        lines.append("")
        lines.append("### Significance")
        lines.append("")
        lines.append("[Explain the significance of the findings]")
        lines.append("")
        lines.append("### Contact Information")
        lines.append("")
        lines.append("[Project contact name and information]")
        lines.append("")
        lines.append("---")
        lines.append("*This press release is a template. Please fill in specific details before publication.*")
        
        return "\n".join(lines)
    
    def create_exhibition_labels(self, artifacts: List[Dict]) -> List[Dict]:
        """Create exhibition labels for artifacts."""
        labels = []
        
        for artifact in artifacts:
            label = {
                'artifact_id': artifact.get('artifact_id', 'Unknown'),
                'title': artifact.get('title', artifact.get('material', 'Artifact')),
                'description': self._create_label_description(artifact),
                'period': artifact.get('period', 'Unknown period'),
                'provenance': artifact.get('context', 'Unknown context')
            }
            labels.append(label)
        
        return labels
    
    def _create_label_description(self, artifact: Dict) -> str:
        """Create description text for artifact label."""
        material = artifact.get('material', 'artifact')
        description = f"This {material} artifact"
        
        if artifact.get('function'):
            description += f" was used for {artifact['function']}"
        
        if artifact.get('period'):
            description += f" during the {artifact['period']}"
        
        description += ". "
        
        if artifact.get('significance'):
            description += artifact['significance']
        else:
            description += "It provides insight into the daily lives of past people."
        
        return description
    
    def generate_social_media_content(self, project_data: Dict, platform: str = 'twitter') -> List[str]:
        """Generate social media content posts."""
        posts = []
        
        project_name = project_data.get('project_name', 'Archaeological Investigation')
        sites_count = len(project_data.get('sites', []))
        
        if platform.lower() == 'twitter' or platform.lower() == 'x':
            char_limit = 280
        elif platform.lower() == 'facebook':
            char_limit = 500
        else:
            char_limit = 280
        
        # Post 1: Announcement
        post1 = f"Exciting archaeological work at {project_name}! "
        if sites_count > 0:
            post1 += f"{sites_count} site(s) documented so far. "
        post1 += "Stay tuned for updates! 🏛️ #Archaeology"
        
        if len(post1) <= char_limit:
            posts.append(post1)
        
        # Post 2: Findings
        if sites_count > 0:
            post2 = f"New discoveries at {project_name}! "
            post2 += "Each find tells a story about the past. "
            post2 += "Learn more about preserving our heritage. 🏺"
            if len(post2) <= char_limit:
                posts.append(post2)
        
        return posts

