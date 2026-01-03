"""
Artifact Assessment Module
Handles "Found Something?" feature with photo upload and text description inputs
"""

import os
from typing import Dict, Optional, List
from PIL import Image
import base64
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArtifactAssessment:
    """Assesses archaeological artifacts from photos or text descriptions."""
    
    def __init__(self, rag_chain=None):
        self.rag_chain = rag_chain
        
    def assess_from_photo(self, image: Image.Image, context: Optional[Dict] = None) -> Dict:
        """Assess artifact from uploaded photo."""
        assessment = {
            'input_type': 'photo',
            'image_size': image.size,
            'image_format': image.format,
            'analysis': {},
            'recommendations': [],
        }
        
        # Extract basic image features
        assessment['analysis']['dimensions'] = image.size
        assessment['analysis']['color_mode'] = image.mode
        assessment['analysis']['file_size_estimate'] = len(image.tobytes())
        
        # Basic color analysis
        if image.mode == 'RGB':
            pixels = list(image.getdata())
            assessment['analysis']['dominant_colors'] = self._get_dominant_colors(pixels, k=3)
        
        # Shape analysis (simplified - could be enhanced with CV)
        assessment['analysis']['aspect_ratio'] = image.size[0] / image.size[1] if image.size[1] > 0 else 1.0
        assessment['analysis']['orientation'] = 'landscape' if image.size[0] > image.size[1] else 'portrait' if image.size[1] > image.size[0] else 'square'
        
        # Generate assessment text for RAG
        if self.rag_chain:
            assessment_text = self._generate_assessment_text(assessment, context)
            assessment['textual_description'] = assessment_text
            
            # Use RAG chain for detailed analysis
            prompt = self._build_assessment_prompt(assessment_text, context)
            try:
                result = self.rag_chain.query(prompt)
                assessment['detailed_analysis'] = result.get('answer', '')
                assessment['sources'] = result.get('source_documents', [])
            except Exception as e:
                logger.error(f"Error in RAG assessment: {e}")
                assessment['detailed_analysis'] = "Analysis available but detailed assessment requires document context."
        else:
            assessment['detailed_analysis'] = "Upload a document to enable detailed artifact analysis."
        
        # Generate recommendations
        assessment['recommendations'] = self._generate_recommendations(assessment, context)
        
        return assessment
    
    def assess_from_text(self, description: Dict, rag_chain=None) -> Dict:
        """Assess artifact from text description with guided questions."""
        assessment = {
            'input_type': 'text',
            'description': description,
            'analysis': {},
            'recommendations': [],
        }
        
        # Build comprehensive description
        full_description = self._build_description(description)
        assessment['analysis']['full_description'] = full_description
        
        # Use RAG chain for analysis
        if rag_chain or self.rag_chain:
            chain = rag_chain or self.rag_chain
            prompt = self._build_assessment_prompt(full_description, description)
            try:
                result = chain.query(prompt)
                assessment['detailed_analysis'] = result.get('answer', '')
                assessment['sources'] = result.get('source_documents', [])
            except Exception as e:
                logger.error(f"Error in RAG assessment: {e}")
                assessment['detailed_analysis'] = "Analysis available but detailed assessment requires document context."
        else:
            assessment['detailed_analysis'] = "Upload a document to enable detailed artifact analysis."
        
        # Generate recommendations
        assessment['recommendations'] = self._generate_recommendations(assessment, description)
        
        return assessment
    
    def _get_dominant_colors(self, pixels: List, k: int = 3) -> List[Dict]:
        """Get dominant colors from image (simplified version)."""
        # Simple color extraction - for production, consider using clustering (KMeans)
        color_counts = {}
        sample_size = min(1000, len(pixels))
        
        for pixel in pixels[:sample_size]:
            if isinstance(pixel, tuple) and len(pixel) >= 3:
                # Quantize colors to reduce complexity
                quantized = tuple((p // 32) * 32 for p in pixel[:3])
                color_counts[quantized] = color_counts.get(quantized, 0) + 1
        
        # Sort by frequency and return top k
        sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'rgb': color, 'frequency': count} for color, count in sorted_colors[:k]]
    
    def _generate_assessment_text(self, photo_analysis: Dict, context: Optional[Dict]) -> str:
        """Generate textual description from photo analysis."""
        parts = []
        
        parts.append(f"Image dimensions: {photo_analysis['analysis']['dimensions']}")
        parts.append(f"Orientation: {photo_analysis['analysis']['orientation']}")
        
        if 'dominant_colors' in photo_analysis['analysis']:
            colors = photo_analysis['analysis']['dominant_colors']
            color_desc = ", ".join([f"RGB{col['rgb']}" for col in colors])
            parts.append(f"Dominant colors: {color_desc}")
        
        if context:
            if context.get('material'):
                parts.append(f"Material: {context['material']}")
            if context.get('size'):
                parts.append(f"Size: {context['size']}")
            if context.get('location'):
                parts.append(f"Location: {context['location']}")
            if context.get('markings'):
                parts.append(f"Markings/Decorations: {context['markings']}")
        
        return ". ".join(parts)
    
    def _build_description(self, description: Dict) -> str:
        """Build comprehensive description from guided questions."""
        parts = []
        
        if description.get('material'):
            parts.append(f"Material: {description['material']}")
        if description.get('size'):
            parts.append(f"Size: {description['size']}")
        if description.get('location'):
            parts.append(f"Location found: {description['location']}")
        if description.get('markings'):
            parts.append(f"Markings or decorations: {description['markings']}")
        if description.get('additional_notes'):
            parts.append(f"Additional notes: {description['additional_notes']}")
        
        return ". ".join(parts)
    
    def _build_assessment_prompt(self, description: str, context: Optional[Dict]) -> str:
        """Build prompt for RAG chain artifact assessment."""
        prompt = (
            "You are an archaeological artifact identification assistant. "
            "Analyze the following artifact description and provide:\n"
            "1. Possible artifact type and identification\n"
            "2. Likely time period or cultural context\n"
            "3. Significance and importance\n"
            "4. Recommended next steps (preservation, documentation, reporting)\n"
            "5. Any legal or ethical considerations\n\n"
            f"Artifact description:\n{description}\n\n"
            "Please provide a detailed, professional assessment."
        )
        
        if context and context.get('location'):
            prompt += f"\n\nLocation context: {context['location']}"
        
        return prompt
    
    def _generate_recommendations(self, assessment: Dict, context: Optional[Dict]) -> List[str]:
        """Generate actionable recommendations based on assessment."""
        recommendations = []
        
        recommendations.append("Document the find with detailed photographs from multiple angles")
        recommendations.append("Record precise location using GPS coordinates")
        recommendations.append("Note the stratigraphic context if applicable")
        
        if context:
            if context.get('location') == 'garden' or context.get('location') == 'construction site':
                recommendations.append("Consider reporting to local archaeological authorities")
                recommendations.append("Document the exact context before removal")
            
            if not context.get('markings'):
                recommendations.append("Look for any markings, inscriptions, or decorative elements")
        
        recommendations.append("Handle with care to avoid damage")
        recommendations.append("Store in appropriate conditions (dry, stable temperature)")
        recommendations.append("Consult with archaeological experts for definitive identification")
        
        return recommendations
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string for display."""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    
    def get_guided_questions_template(self) -> Dict:
        """Get template for guided questions."""
        return {
            'material': {
                'question': 'What material is it?',
                'options': ['stone', 'metal', 'pottery', 'bone', 'glass', 'organic', 'other'],
                'required': True,
            },
            'size': {
                'question': 'How big is it?',
                'options': ['coin-sized', 'hand-sized', 'larger', 'very large'],
                'required': True,
            },
            'location': {
                'question': 'Where did you find it?',
                'options': ['garden', 'construction site', 'beach', 'field', 'archaeological site', 'other'],
                'required': True,
            },
            'markings': {
                'question': 'Any markings or decorations?',
                'options': None,  # Free text
                'required': False,
            },
            'additional_notes': {
                'question': 'Additional notes or observations',
                'options': None,  # Free text
                'required': False,
            },
        }

