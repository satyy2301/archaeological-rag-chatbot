"""
Report Generator Module
Auto-generates archaeological reports with templates, citations, and data integration
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates archaeological reports from project data."""
    
    REPORT_TYPES = {
        'survey': 'Survey Report',
        'excavation': 'Excavation Report',
        'compliance': 'Compliance Report',
        'field_notes': 'Field Notes Summary',
        'findings': 'Findings Report',
        'methodology': 'Methodology Report',
        'academic': 'Academic Paper',
    }
    
    def __init__(self, rag_chain=None):
        self.rag_chain = rag_chain
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict:
        """Load default report templates."""
        return {
            'survey': {
                'title': 'Archaeological Survey Report',
                'sections': [
                    'Executive Summary',
                    'Introduction',
                    'Methodology',
                    'Site Descriptions',
                    'Findings',
                    'Analysis',
                    'Recommendations',
                    'Conclusion',
                    'References',
                    'Appendices'
                ]
            },
            'excavation': {
                'title': 'Excavation Report',
                'sections': [
                    'Executive Summary',
                    'Introduction',
                    'Site Location and Setting',
                    'Excavation Methodology',
                    'Stratigraphy',
                    'Features and Contexts',
                    'Artifacts',
                    'Dating',
                    'Interpretation',
                    'Recommendations',
                    'References',
                    'Appendices'
                ]
            },
            'compliance': {
                'title': 'Compliance Report',
                'sections': [
                    'Project Overview',
                    'Permit Information',
                    'Methodology',
                    'Findings',
                    'Compliance Status',
                    'Recommendations',
                    'Appendices'
                ]
            },
            'field_notes': {
                'title': 'Field Notes Summary',
                'sections': [
                    'Daily Log Summary',
                    'Key Findings',
                    'Observations',
                    'Issues and Challenges',
                    'Next Steps'
                ]
            },
        }
    
    def generate_report(self, report_type: str, project_data: Dict, 
                       custom_sections: Optional[List[str]] = None,
                       template_style: str = 'standard') -> str:
        """Generate a report from project data."""
        
        if report_type not in self.REPORT_TYPES:
            report_type = 'survey'
        
        template = self.templates.get(report_type, self.templates['survey'])
        sections = custom_sections or template['sections']
        
        report_lines = []
        
        # Title
        report_lines.append(f"# {template['title']}")
        report_lines.append("")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Generate each section
        for section in sections:
            report_lines.append(f"## {section}")
            report_lines.append("")
            
            section_content = self._generate_section_content(
                section, project_data, report_type
            )
            report_lines.append(section_content)
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _generate_section_content(self, section: str, project_data: Dict, 
                                 report_type: str) -> str:
        """Generate content for a specific section."""
        
        content_lines = []
        
        if section == "Executive Summary":
            content_lines.append(self._generate_executive_summary(project_data))
        
        elif section == "Introduction":
            content_lines.append(self._generate_introduction(project_data))
        
        elif section == "Methodology":
            content_lines.append(self._generate_methodology(project_data))
        
        elif section == "Site Descriptions":
            sites = project_data.get('sites', [])
            if sites:
                for site in sites:
                    content_lines.append(f"### {site.get('site_name', 'Unnamed Site')}")
                    content_lines.append(f"**Location:** {site.get('latitude', 'N/A')}, {site.get('longitude', 'N/A')}")
                    if site.get('description'):
                        content_lines.append(site['description'])
                    content_lines.append("")
            else:
                content_lines.append("No site data available.")
        
        elif section == "Findings":
            artifacts = project_data.get('artifacts', [])
            if artifacts:
                content_lines.append(f"Total artifacts recorded: {len(artifacts)}")
                content_lines.append("")
                # Group by type
                by_type = {}
                for artifact in artifacts:
                    artifact_type = artifact.get('type', 'Unknown')
                    by_type.setdefault(artifact_type, []).append(artifact)
                
                for artifact_type, items in by_type.items():
                    content_lines.append(f"### {artifact_type}")
                    content_lines.append(f"Count: {len(items)}")
                    content_lines.append("")
            else:
                content_lines.append("No artifact data available.")
        
        elif section == "Analysis":
            if self.rag_chain:
                analysis_prompt = self._build_analysis_prompt(project_data, report_type)
                try:
                    result = self.rag_chain.query(analysis_prompt)
                    content_lines.append(result.get('answer', 'Analysis pending.'))
                except Exception as e:
                    logger.error(f"Error generating analysis: {e}")
                    content_lines.append("Analysis generation requires document context.")
            else:
                content_lines.append("Upload documents to enable automated analysis generation.")
        
        elif section == "Recommendations":
            content_lines.append(self._generate_recommendations(project_data, report_type))
        
        elif section == "References":
            content_lines.append(self._generate_references(project_data))
        
        elif section == "Appendices":
            content_lines.append(self._generate_appendices(project_data))
        
        else:
            # Generic section
            content_lines.append(f"Content for {section} section.")
            if section.lower() in project_data:
                content_lines.append(str(project_data[section.lower()]))
        
        return "\n".join(content_lines)
    
    def _generate_executive_summary(self, project_data: Dict) -> str:
        """Generate executive summary."""
        lines = []
        lines.append("This report presents the findings from the archaeological investigation.")
        
        sites_count = len(project_data.get('sites', []))
        artifacts_count = len(project_data.get('artifacts', []))
        
        if sites_count > 0:
            lines.append(f"A total of {sites_count} site(s) were documented during this investigation.")
        
        if artifacts_count > 0:
            lines.append(f"{artifacts_count} artifact(s) were recorded and analyzed.")
        
        project_name = project_data.get('project_name', 'the project')
        lines.append(f"Key findings and recommendations are detailed in the following sections.")
        
        return " ".join(lines)
    
    def _generate_introduction(self, project_data: Dict) -> str:
        """Generate introduction section."""
        lines = []
        project_name = project_data.get('project_name', 'Archaeological Investigation')
        lines.append(f"This report documents the results of {project_name}.")
        
        if project_data.get('location'):
            lines.append(f"The investigation was conducted at {project_data['location']}.")
        
        if project_data.get('date_range'):
            lines.append(f"Field work was conducted during {project_data['date_range']}.")
        
        lines.append("The following sections provide detailed information about the methodology, findings, and recommendations.")
        
        return " ".join(lines)
    
    def _generate_methodology(self, project_data: Dict) -> str:
        """Generate methodology section."""
        lines = []
        
        methodology = project_data.get('methodology', {})
        if methodology:
            if methodology.get('survey_type'):
                lines.append(f"Survey Type: {methodology['survey_type']}")
            if methodology.get('equipment'):
                lines.append(f"Equipment: {', '.join(methodology['equipment'])}")
            if methodology.get('team_size'):
                lines.append(f"Team Size: {methodology['team_size']}")
        
        if not lines:
            lines.append("Methodological details should be documented here.")
            lines.append("Include information about survey methods, equipment used, team composition, and data recording procedures.")
        
        return "\n".join(lines)
    
    def _generate_recommendations(self, project_data: Dict, report_type: str) -> str:
        """Generate recommendations section."""
        lines = []
        
        recommendations = project_data.get('recommendations', [])
        if recommendations:
            for idx, rec in enumerate(recommendations, 1):
                lines.append(f"{idx}. {rec}")
        else:
            lines.append("Based on the findings, the following recommendations are made:")
            lines.append("")
            lines.append("1. Continue monitoring of documented sites")
            lines.append("2. Conduct further investigation if warranted")
            lines.append("3. Ensure proper documentation and curation of artifacts")
            lines.append("4. Consider public engagement and education opportunities")
        
        return "\n".join(lines)
    
    def _generate_references(self, project_data: Dict) -> str:
        """Generate references section."""
        lines = []
        
        references = project_data.get('references', [])
        if references:
            for ref in references:
                lines.append(f"- {ref}")
        else:
            lines.append("References should be listed here using standard archaeological citation formats.")
            lines.append("Include all sources cited in the report.")
        
        return "\n".join(lines)
    
    def _generate_appendices(self, project_data: Dict) -> str:
        """Generate appendices section."""
        lines = []
        lines.append("### Appendix A: Site Locations")
        lines.append("Detailed coordinates and site information.")
        lines.append("")
        lines.append("### Appendix B: Artifact Catalog")
        lines.append("Complete catalog of recorded artifacts.")
        lines.append("")
        lines.append("### Appendix C: Maps and Figures")
        lines.append("Supporting maps, photographs, and figures.")
        
        return "\n".join(lines)
    
    def _build_analysis_prompt(self, project_data: Dict, report_type: str) -> str:
        """Build prompt for RAG-based analysis generation."""
        prompt = (
            f"Generate a comprehensive analysis section for an archaeological {report_type} report. "
            f"Consider the following project data:\n\n"
            f"Project: {project_data.get('project_name', 'Unknown')}\n"
            f"Sites: {len(project_data.get('sites', []))}\n"
            f"Artifacts: {len(project_data.get('artifacts', []))}\n\n"
            "Provide analysis of findings, significance, context, and interpretation. "
            "Use professional archaeological language and cite relevant methodologies."
        )
        return prompt
    
    def generate_citation(self, author: str, year: str, title: str, 
                         publisher: Optional[str] = None,
                         journal: Optional[str] = None,
                         style: str = 'harvard') -> str:
        """Generate formatted citation."""
        if style.lower() == 'harvard':
            if journal:
                return f"{author} ({year}), '{title}', {journal}."
            elif publisher:
                return f"{author} ({year}), {title}, {publisher}."
            else:
                return f"{author} ({year}), {title}."
        elif style.lower() == 'chicago':
            if journal:
                return f"{author}. \"{title}.\" {journal} ({year})."
            elif publisher:
                return f"{author}. {title}. {publisher}, {year}."
            else:
                return f"{author}. {title}. {year}."
        else:
            # Default format
            return f"{author} ({year}). {title}."
    
    def export_report(self, report_content: str, output_path: str, format: str = 'markdown') -> bool:
        """Export report to file."""
        try:
            if format.lower() == 'markdown' or format.lower() == 'md':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
            elif format.lower() == 'txt':
                # Convert markdown to plain text (simple)
                text_content = report_content
                # Remove markdown headers
                import re
                text_content = re.sub(r'^#+\s*', '', text_content, flags=re.MULTILINE)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
            else:
                # Default to markdown
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
            
            logger.info(f"Report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return False
    
    def create_report_from_template(self, template_name: str, project_data: Dict) -> str:
        """Create report using a specific template."""
        return self.generate_report(template_name, project_data)

