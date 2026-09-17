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

from artifact_lookup import ArtifactLookupClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArtifactAssessment:
    """Assesses archaeological artifacts from photos or text descriptions."""
    
    def __init__(self, rag_chain=None):
        self.rag_chain = rag_chain
        self.lookup_client = ArtifactLookupClient()
        
    def assess_from_photo(self, image: Image.Image, context: Optional[Dict] = None) -> Dict:
        """Assess artifact from uploaded photo with CV/AI enhancements and optional RAG."""
        from image_analyzer import analyze, to_png_bytes  # local import to keep module lightweight

        script_profile = (context or {}).get('script_profile', 'auto')

        assessment = {
            'input_type': 'photo',
            'image_size': image.size,
            'image_format': image.format,
            'analysis': {},
            'recommendations': [],
            'visuals': {},
        }

        # Core image analysis pipeline
        try:
            result = analyze(image, script_profile=script_profile, force_ocr=True)
            assessment['analysis']['dimensions'] = image.size
            assessment['analysis']['color_mode'] = image.mode
            assessment['analysis']['file_size_estimate'] = len(image.tobytes())
            assessment['analysis']['aspect_ratio'] = image.size[0] / image.size[1] if image.size[1] > 0 else 1.0
            assessment['analysis']['orientation'] = 'landscape' if image.size[0] > image.size[1] else 'portrait' if image.size[1] > image.size[0] else 'square'
            assessment['analysis']['script_profile'] = script_profile

            # Dominant colors (quick estimate)
            if image.mode == 'RGB':
                pixels = list(image.getdata())
                assessment['analysis']['dominant_colors'] = self._get_dominant_colors(pixels, k=3)

            # OCR boxes and coin hints
            ocr_payload = result.get('ocr', {})
            assessment['analysis']['ocr'] = ocr_payload.get('regions', [])
            assessment['analysis']['ocr_backend'] = ocr_payload.get('backend', 'unknown')
            assessment['analysis']['ocr_notes'] = ocr_payload.get('notes', '')
            assessment['analysis']['coin_detection'] = result.get('coin', {})
            assessment['analysis']['detected_text'] = self._collect_detected_text(assessment['analysis']['ocr'])

            # Visuals (PNG bytes for Streamlit display)
            visuals = {
                'pre_denosed': to_png_bytes(result['preprocessed'].get('denoised', image)),
                'pre_shadow_reduced': to_png_bytes(result['preprocessed'].get('shadow_reduced', image)),
                'pre_normalized': to_png_bytes(result['preprocessed'].get('normalized', image)),
                'enh_clahe': to_png_bytes(result['enhancements']['clahe']),
                'enh_retinex': to_png_bytes(result['enhancements']['retinex']),
                'enh_sharpen': to_png_bytes(result['enhancements']['sharpen']),
                'boxed': to_png_bytes(result['boxed']),
            }
            assessment['visuals'] = visuals

            lookup_query = self._build_lookup_query(assessment['analysis'], context)
            assessment['similar_finds'] = self.lookup_client.search_similar_finds(lookup_query, context=context, limit=6)
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            assessment['similar_finds'] = []

        # Optional RAG-based narrative
        if self.rag_chain:
            assessment_text = self._generate_assessment_text(assessment, context)
            assessment['textual_description'] = assessment_text
            prompt = self._build_assessment_prompt(assessment_text, context)
            try:
                result = self.rag_chain.query(prompt)
                assessment['detailed_analysis'] = result.get('answer', '')
                assessment['sources'] = result.get('source_documents', [])
            except Exception as e:
                logger.error(f"Error in RAG assessment: {e}")
                assessment['detailed_analysis'] = "Computer-vision analysis completed. Document-based reasoning unavailable."
        else:
            assessment['detailed_analysis'] = self._build_visual_assessment_summary(assessment, context)

        # Layman-first summary for top-of-page rendering
        assessment['layman_summary_sections'] = self._build_layman_summary_sections(assessment, context)
        assessment['layman_summary'] = self._format_layman_summary_markdown(assessment['layman_summary_sections'])

        # Recommendations
        assessment['recommendations'] = self._generate_recommendations(assessment, context)
        return assessment

    def _collect_detected_text(self, ocr_regions: List[Dict]) -> str:
        """Collect confident OCR readings into a compact lookup string."""
        parts = []
        for item in ocr_regions:
            text = (item.get('text') or '').strip()
            if text and float(item.get('confidence', 0.0)) >= 0.2:
                parts.append(text)
        return " ".join(parts[:8])

    def _build_lookup_query(self, analysis: Dict, context: Optional[Dict]) -> str:
        """Create an external lookup query from OCR, material, and notes."""
        bits = []
        detected_text = analysis.get('detected_text') or ''
        if detected_text:
            bits.append(detected_text)
        if context:
            for key in ('material', 'markings', 'size', 'artifact_type'):
                value = context.get(key)
                if value:
                    bits.append(str(value))
        if not bits:
            orientation = analysis.get('orientation')
            if orientation:
                bits.append(str(orientation))
        return ' '.join(bits).strip()

    def _color_tone_from_dominant(self, dominant_colors: Optional[List[Dict]]) -> str:
        """Describe dominant colors in everyday language."""
        if not dominant_colors:
            return ""

        top = dominant_colors[0].get('rgb')
        if not top or len(top) < 3:
            return ""

        r, g, b = top[:3]
        brightness = (r + g + b) / 3
        if brightness < 70:
            tone = "dark"
        elif brightness < 150:
            tone = "medium-toned"
        else:
            tone = "light"

        if abs(r - g) < 25 and abs(g - b) < 25:
            material_hint = "stone- or earth-like"
        elif r > g + 30 and r > b + 30:
            material_hint = "reddish or bronze-like"
        elif b > r + 20 and b > g + 20:
            material_hint = "cool metal-like"
        elif brightness < 90:
            material_hint = "dark metal-like"
        else:
            material_hint = "mixed surface"

        return f"The surface looks {tone} with {material_hint} coloring."

    def _compute_confidence_signals(
        self, analysis: Dict, context: Optional[Dict], similar_count: int
    ) -> Dict:
        """Score evidence used for confidence and reasoning."""
        artifact_hint = (context or {}).get('artifact_type', '')
        circles = analysis.get('coin_detection', {}).get('circles') or []
        detected_text = (analysis.get('detected_text') or '').strip()
        has_material = bool((context or {}).get('material'))

        score = 0
        if artifact_hint and artifact_hint != 'unknown':
            score += 2
        if circles:
            score += 2
        if detected_text:
            score += 1
        if similar_count > 0:
            score += 1
        if has_material:
            score += 1

        if score >= 5:
            level = "High"
        elif score >= 3:
            level = "Medium"
        else:
            level = "Low"

        return {
            'score': score,
            'level': level,
            'has_round_shape': bool(circles),
            'has_detected_text': bool(detected_text),
            'has_artifact_hint': bool(artifact_hint and artifact_hint != 'unknown'),
            'artifact_hint': artifact_hint,
            'similar_count': similar_count,
            'has_material': has_material,
            'material': (context or {}).get('material', ''),
        }

    def _describe_visible_features(self, analysis: Dict, context: Optional[Dict]) -> str:
        """Describe what is visible in the photo using plain English."""
        sentences = []
        orientation = analysis.get('orientation', '')
        if orientation == 'portrait':
            sentences.append("Your photo shows an object photographed upright in portrait orientation.")
        elif orientation == 'landscape':
            sentences.append("Your photo shows an object photographed in landscape orientation.")
        elif orientation == 'square':
            sentences.append("Your photo shows an object photographed in a square frame.")

        color_tone = self._color_tone_from_dominant(analysis.get('dominant_colors'))
        if color_tone:
            sentences.append(color_tone)

        circles = analysis.get('coin_detection', {}).get('circles') or []
        if circles:
            sentences.append(
                "The object has a clear round outline, similar to a coin, medal, or medallion."
            )

        detected_text = (analysis.get('detected_text') or '').strip()
        if detected_text:
            sentences.append(
                f"Some markings or lettering may be visible. The clearest reading found was: \"{detected_text}\"."
            )
        elif analysis.get('ocr'):
            sentences.append(
                "The image has areas that may contain markings, but the text is faint or hard to read clearly."
            )

        if context:
            context_bits = []
            if context.get('material'):
                context_bits.append(f"material: {context['material']}")
            if context.get('size'):
                context_bits.append(f"size: {context['size']}")
            if context.get('location'):
                context_bits.append(f"found in/on: {context['location']}")
            if context.get('markings'):
                context_bits.append(f"noted markings: {context['markings']}")
            if context_bits:
                sentences.append(
                    "You also shared helpful context — " + "; ".join(context_bits) + "."
                )

        if not sentences:
            sentences.append(
                "We received your photo, but the visible details are limited. "
                "Adding context (material, size, where it was found) can improve the assessment."
            )

        return " ".join(sentences)

    def _describe_likely_identification(self, analysis: Dict, context: Optional[Dict]) -> str:
        """Describe the most likely artifact type in full sentences."""
        circles = analysis.get('coin_detection', {}).get('circles') or []
        detected_text = (analysis.get('detected_text') or '').strip()
        artifact_hint = (context or {}).get('artifact_type', '')

        if artifact_hint and artifact_hint != 'unknown':
            return (
                f"Based on your description and the photo, this most likely is a {artifact_hint}. "
                "We still recommend comparing it with similar records and expert references."
            )
        if circles and detected_text:
            return (
                "This most likely is a small round object such as a coin or medallion. "
                "The round shape and visible lettering or design support that idea."
            )
        if circles:
            return (
                "This most likely is a coin or medallion, based on its round shape. "
                "The photo alone cannot confirm the exact type, date, or origin."
            )
        if detected_text:
            return (
                "This most likely is an inscribed or marked object, such as a seal, tablet fragment, "
                "or decorated piece. The visible markings are an important clue."
            )
        return (
            "From this photo alone, we cannot name the exact artifact type with confidence. "
            "It appears to be an archaeological or historical object that needs closer review."
        )

    def _describe_confidence(self, signals: Dict) -> tuple:
        """Return confidence level and a plain-English explanation."""
        level = signals['level']
        strong_points = []
        weak_points = []

        if signals['has_round_shape']:
            strong_points.append("the round shape is clear")
        if signals['has_detected_text']:
            strong_points.append("some markings or text are visible")
        if signals['has_artifact_hint']:
            strong_points.append(f"you identified it as a {signals['artifact_hint']}")
        if signals['similar_count'] > 0:
            strong_points.append(
                f"{signals['similar_count']} similar items appear in public museum records"
            )
        if signals['has_material']:
            strong_points.append(f"you provided material context ({signals['material']})")

        if not signals['has_round_shape'] and not signals['has_detected_text']:
            weak_points.append("the photo does not show a clear shape or readable markings")
        if signals['similar_count'] == 0:
            weak_points.append("no close matches were found in public collections from this query")
        if not signals['has_material']:
            weak_points.append("material and size details were not provided")

        explanation_parts = [f"{level} confidence."]
        if strong_points:
            explanation_parts.append(
                "What supports this: " + "; ".join(strong_points) + "."
            )
        if weak_points and level != "High":
            explanation_parts.append(
                "What is still uncertain: " + "; ".join(weak_points[:2]) + "."
            )
        if level != "High":
            explanation_parts.append(
                "A photo alone usually cannot confirm exact type, date, or cultural origin."
            )

        return level, " ".join(explanation_parts)

    def _describe_why_we_think_this(
        self, analysis: Dict, context: Optional[Dict], similar_count: int
    ) -> str:
        """Build bullet-style reasoning in readable prose."""
        bullets = []
        circles = analysis.get('coin_detection', {}).get('circles') or []
        detected_text = (analysis.get('detected_text') or '').strip()

        if circles:
            bullets.append("- The object has a clear round outline, like a coin or medal.")
        if detected_text:
            bullets.append("- Markings or lettering appear on the surface.")
        elif analysis.get('ocr'):
            bullets.append("- The image shows areas that may contain inscriptions or decoration.")
        if similar_count:
            bullets.append(
                f"- {similar_count} similar items were found in public museum records."
            )
        if context and context.get('material'):
            bullets.append(f"- You noted the material as {context['material']}.")
        if context and context.get('artifact_type') and context['artifact_type'] != 'unknown':
            bullets.append(f"- You suggested this may be a {context['artifact_type']}.")

        if not bullets:
            bullets.append(
                "- The photo was analyzed, but the visible clues are limited. "
                "More context or a clearer image would help."
            )

        return "\n".join(bullets)

    def _describe_similar_finds_blurb(self, similar_finds: List[Dict]) -> str:
        """Mention example similar finds in plain language."""
        if not similar_finds:
            return ""

        examples = []
        for item in similar_finds[:2]:
            title = item.get('title', 'Untitled result')
            source = item.get('source', 'a public collection')
            examples.append(f"\"{title}\" ({source})")

        if len(examples) == 1:
            return f"One example from public records is {examples[0]}."
        return f"Examples from public records include {examples[0]} and {examples[1]}."

    def _describe_next_steps(
        self, analysis: Dict, context: Optional[Dict], has_similar_finds: bool
    ) -> str:
        """Suggest practical next steps in simple language."""
        steps = [
            "Look at the enhanced images below to see faint details more clearly.",
        ]
        if has_similar_finds:
            steps.append(
                "Compare your object with the Similar Finds section to see if any records look close."
            )
        else:
            steps.append(
                "Try adding clearer markings, material, or size details to improve matching."
            )
        steps.append(
            "If you know where it was found, note the location and keep the object in its original context when possible."
        )
        steps.append(
            "Avoid cleaning, rubbing, or polishing the object before an expert reviews it."
        )
        if not (context or {}).get('markings') and not analysis.get('detected_text'):
            steps.append(
                "Take additional photos in good, even light from several angles."
            )
        return " ".join(steps)

    def _build_layman_summary_sections(self, assessment: Dict, context: Optional[Dict]) -> Dict:
        """Create structured plain-language sections for the UI."""
        analysis = assessment.get('analysis', {})
        similar_finds = assessment.get('similar_finds') or []
        similar_count = len(similar_finds)
        signals = self._compute_confidence_signals(analysis, context, similar_count)
        confidence_level, confidence_explanation = self._describe_confidence(signals)

        what_we_see = self._describe_visible_features(analysis, context)
        similar_blurb = self._describe_similar_finds_blurb(similar_finds)
        if similar_blurb:
            what_we_see = f"{what_we_see} {similar_blurb}"

        return {
            'what_we_see': what_we_see,
            'likely_identification': self._describe_likely_identification(analysis, context),
            'confidence_level': confidence_level,
            'confidence_explanation': confidence_explanation,
            'why_we_think_this': self._describe_why_we_think_this(analysis, context, similar_count),
            'suggested_next_steps': self._describe_next_steps(
                analysis, context, has_similar_finds=similar_count > 0
            ),
        }

    def _build_text_layman_summary_sections(self, description: Dict) -> Dict:
        """Create plain-language sections for text-only artifact submissions."""
        material = description.get('material', '')
        size = description.get('size', '')
        location = description.get('location', '')
        markings = (description.get('markings') or '').strip()
        notes = (description.get('additional_notes') or '').strip()

        visible_parts = []
        if material:
            visible_parts.append(f"You described the material as {material}.")
        if size:
            visible_parts.append(f"You said it is about {size}.")
        if location:
            visible_parts.append(f"You found it in or on a {location}.")
        if markings:
            visible_parts.append(f"You noted these markings or decorations: {markings}.")
        if notes:
            visible_parts.append(f"Additional notes: {notes}.")
        what_we_see = (
            " ".join(visible_parts)
            if visible_parts
            else "You shared a short description of your find."
        )

        if markings:
            likely = (
                "This may be an inscribed or decorated object. "
                "The markings you described are an important clue for identification."
            )
        elif material == 'metal' and size == 'coin-sized':
            likely = "This may be a small metal object such as a coin, token, or medallion."
        elif material == 'pottery':
            likely = "This may be a pottery fragment or vessel piece."
        elif material == 'stone':
            likely = "This may be a stone tool, carving, or architectural fragment."
        else:
            likely = (
                "Based on your description, this appears to be an archaeological or historical find "
                "that would benefit from expert review."
            )

        score = sum([
            1 if material else 0,
            1 if size else 0,
            1 if location else 0,
            2 if markings else 0,
            1 if notes else 0,
        ])
        if score >= 5:
            level = "Medium"
        elif score >= 3:
            level = "Low"
        else:
            level = "Low"

        confidence_explanation = (
            f"{level} confidence. "
            "Text descriptions are helpful, but photos and expert review are usually needed "
            "for a reliable identification."
        )

        why_bits = []
        if material:
            why_bits.append(f"- Material noted: {material}.")
        if size:
            why_bits.append(f"- Size noted: {size}.")
        if location:
            why_bits.append(f"- Find location noted: {location}.")
        if markings:
            why_bits.append("- You described visible markings or decoration.")
        if not why_bits:
            why_bits.append("- Limited details were provided in the description.")

        next_steps = (
            "If possible, upload a clear photo in good light. "
            "Record where the object was found, handle it carefully, and avoid cleaning it. "
            "Consider sharing your find with a local archaeologist or museum for confirmation."
        )

        return {
            'what_we_see': what_we_see,
            'likely_identification': likely,
            'confidence_level': level,
            'confidence_explanation': confidence_explanation,
            'why_we_think_this': "\n".join(why_bits),
            'suggested_next_steps': next_steps,
        }

    def _format_layman_summary_markdown(self, sections: Dict) -> str:
        """Join structured sections into markdown for backward compatibility."""
        return "\n\n".join([
            f"**What we see:** {sections.get('what_we_see', '')}",
            f"**What this likely is:** {sections.get('likely_identification', '')}",
            f"**How confident we are:** {sections.get('confidence_level', '')}. "
            f"{sections.get('confidence_explanation', '')}",
            f"**Why we think this:**\n{sections.get('why_we_think_this', '')}",
            f"**What to do next:** {sections.get('suggested_next_steps', '')}",
        ])

    def _build_visual_assessment_summary(self, assessment: Dict, context: Optional[Dict]) -> str:
        """Build a friendly narrative when no RAG document context is available."""
        analysis = assessment.get('analysis', {})
        paragraphs = [
            (
                "We reviewed your photo using non-destructive image enhancement. "
                "This means we improved brightness, contrast, and sharpness without changing the original object."
            ),
            (
                "First, the image was cleaned up to reduce noise and uneven shadows. "
                "Then we created three enhanced views: one with stronger contrast, one with more even lighting, "
                "and one with sharper edges to help faint details stand out."
            ),
        ]

        if analysis.get('detected_text'):
            paragraphs.append(
                f"The clearest visible reading we found was: \"{analysis['detected_text']}\". "
                "Some letters or symbols may still be unclear because of wear, lighting, or photo quality."
            )
        elif analysis.get('ocr'):
            paragraphs.append(
                "We marked areas that may contain text or decoration. "
                "If the writing is faint, try the enhanced images below and zoom into numbered regions."
            )

        if analysis.get('coin_detection', {}).get('circles'):
            paragraphs.append(
                "The object has a round outline, which is common for coins, medals, and medallions. "
                "Round shape alone does not confirm the exact type or age."
            )

        if context and context.get('material'):
            paragraphs.append(f"You told us the material may be {context['material']}.")

        similar_finds = assessment.get('similar_finds') or []
        if similar_finds:
            blurb = self._describe_similar_finds_blurb(similar_finds)
            paragraphs.append(
                f"We also searched public museum records. {blurb} "
                "These are approximate matches and should be used for comparison, not as final proof."
            )
        else:
            paragraphs.append(
                "We did not find close matches in public museum records from the current details. "
                "Try adding clearer markings, material, or size information."
            )

        paragraphs.append(
            "This assessment is a starting point. For a definitive identification, compare your photos "
            "with trusted references and consult an archaeological expert."
        )

        return "\n\n".join(paragraphs)
    
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

        assessment['layman_summary_sections'] = self._build_text_layman_summary_sections(description)
        assessment['layman_summary'] = self._format_layman_summary_markdown(
            assessment['layman_summary_sections']
        )
        
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
            if context.get('artifact_type'):
                parts.append(f"Artifact type: {context['artifact_type']}")
            if context.get('script_profile'):
                parts.append(f"Script profile: {context['script_profile']}")
            if context.get('size'):
                parts.append(f"Size: {context['size']}")
            if context.get('location'):
                parts.append(f"Location: {context['location']}")
            if context.get('markings'):
                parts.append(f"Markings/Decorations: {context['markings']}")

        detected_text = photo_analysis['analysis'].get('detected_text')
        if detected_text:
            parts.append(f"Detected visible text: {detected_text}")
        
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
            "You are an archaeological artifact identification assistant writing for a non-expert. "
            "Analyze the following artifact description and provide:\n"
            "1. Possible artifact type and identification\n"
            "2. Likely time period or cultural context\n"
            "3. Significance and importance\n"
            "4. Recommended next steps (preservation, documentation, reporting)\n"
            "5. Any legal or ethical considerations\n\n"
            f"Artifact description:\n{description}\n\n"
            "Write in plain, friendly English. Use short sentences. Avoid jargon. "
            "Clearly state what is known, what is uncertain, and what the user should do next."
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

