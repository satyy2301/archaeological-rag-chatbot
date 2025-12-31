"""
PDF Processing Module for Archaeological Documents
Extracts text from PDF files and prepares it for vectorization.
Also supports simple extraction of coordinates and dates for visualisations.
"""

import logging
import re
from typing import List, Dict

import pdfplumber
import PyPDF2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process PDF files to extract text content and basic structured data."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text_chunks: List[str] = []
        self.full_text: str = ""

    def extract_text_pdfplumber(self) -> str:
        """Extract text using pdfplumber (better for complex layouts)."""
        full_text = ""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                logger.info(f"Processing PDF with {len(pdf.pages)} pages")
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        full_text += f"\n\n--- Page {i+1} ---\n\n{text}"
                    logger.info(f"Extracted text from page {i+1}")
        except Exception as e:
            logger.error(f"Error with pdfplumber: {e}")
            # Fallback to PyPDF2
            return self.extract_text_pypdf2()

        self.full_text = full_text
        return full_text

    def extract_text_pypdf2(self) -> str:
        """Extract text using PyPDF2 (fallback method)."""
        full_text = ""
        try:
            with open(self.pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                logger.info(f"Processing PDF with {len(pdf_reader.pages)} pages")
                for i, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text:
                        full_text += f"\n\n--- Page {i+1} ---\n\n{text}"
                    logger.info(f"Extracted text from page {i+1}")
        except Exception as e:
            logger.error(f"Error with PyPDF2: {e}")
            raise

        self.full_text = full_text
        return full_text

    def extract_text(self) -> str:
        """Main method to extract text from PDF."""
        try:
            return self.extract_text_pdfplumber()
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")
            return self.extract_text_pypdf2()

    def chunk_text(
        self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[str]:
        """
        Split text into chunks for embedding.

        Args:
            text: Full text content
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks to maintain context

        Returns:
            List of text chunks
        """
        if not text:
            return []

        chunks: List[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings near the chunk boundary
                for delimiter in [". ", ".\n", "! ", "!\n", "? ", "?\n", "\n\n"]:
                    last_occurrence = text.rfind(delimiter, start, end)
                    if last_occurrence != -1:
                        end = last_occurrence + len(delimiter)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - chunk_overlap
            if start >= text_length:
                break

        logger.info(f"Created {len(chunks)} text chunks")
        return chunks

    def process(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        Process PDF and return text chunks.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List of text chunks ready for embedding
        """
        text = self.extract_text()
        self.text_chunks = self.chunk_text(text, chunk_size, chunk_overlap)
        return self.text_chunks

    # ------------------------------------------------------------------
    # Lightweight structured extraction helpers for maps & timelines
    # ------------------------------------------------------------------

    def _ensure_full_text(self) -> str:
        """Ensure full_text is populated before running extraction helpers."""
        if not self.full_text:
            self.full_text = self.extract_text()
        return self.full_text

    def _dms_to_decimal(self, degrees: int, minutes: int, seconds: float, direction: str) -> float:
        """Convert degrees-minutes-seconds to decimal degrees."""
        decimal = degrees + minutes / 60.0 + seconds / 3600.0
        if direction.upper() in ['S', 'W']:
            decimal = -decimal
        return decimal

    def extract_coordinates(self, context_window: int = 100) -> List[Dict]:
        """
        Extract latitude/longitude pairs from the PDF text.
        
        Supports multiple formats:
        - Decimal degrees: "28.6128° N, 77.2311° E" or "12.9716, 77.5946"
        - DMS format: "40°42'46\"N 74°00'21\"W" or "N 35°42'12\", E 139°46'35\""
        - UTM coordinates (basic support): "UTM Zone 43N 582639 4512345"
        
        Returns:
            List of dicts with keys: latitude, longitude, context, site_name (if found)
        """
        text = self._ensure_full_text()
        results: List[Dict] = []
        seen_coords = set()  # Avoid duplicates
        
        # Pattern 1: Decimal degrees with N/S/E/W indicators
        # "28.6128° N, 77.2311° E" or "28.6128 N, 77.2311 E"
        decimal_with_dirs = re.compile(
            r'(?P<lat>-?\d{1,2}\.?\d*)\s*°?\s*[,\s]*(?P<lat_dir>[NS])[,\s]*'
            r'(?P<lon>-?\d{1,3}\.?\d*)\s*°?\s*[,\s]*(?P<lon_dir>[EW])',
            re.IGNORECASE | re.MULTILINE
        )
        for match in decimal_with_dirs.finditer(text):
            try:
                lat = float(match.group("lat"))
                lon = float(match.group("lon"))
                lat_dir = match.group("lat_dir").upper()
                lon_dir = match.group("lon_dir").upper()
                
                if lat_dir == 'S':
                    lat = -lat
                if lon_dir == 'W':
                    lon = -lon
                    
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    continue
                    
                coord_key = (round(lat, 6), round(lon, 6))
                if coord_key in seen_coords:
                    continue
                seen_coords.add(coord_key)
                
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context_snippet = text[start:end].replace("\n", " ").strip()
                
                # Try to extract site name from context
                site_name = self._extract_site_name_from_context(context_snippet)
                
                results.append({
                    "latitude": lat,
                    "longitude": lon,
                    "context": context_snippet,
                    "site_name": site_name,
                })
            except (ValueError, AttributeError):
                continue
        
        # Pattern 2: DMS format - "40°42'46\"N 74°00'21\"W" or "N 35°42'12\", E 139°46'35\""
        dms_pattern = re.compile(
            r'(?:N|S|North|South)?\s*(?P<lat_deg>\d{1,2})°\s*(?P<lat_min>\d{1,2})[\'′]\s*(?P<lat_sec>\d{1,2}(?:\.\d+)?)[\"″]?\s*(?P<lat_dir>[NS])'
            r'[,\s]+'
            r'(?:E|W|East|West)?\s*(?P<lon_deg>\d{1,3})°\s*(?P<lon_min>\d{1,2})[\'′]\s*(?P<lon_sec>\d{1,2}(?:\.\d+)?)[\"″]?\s*(?P<lon_dir>[EW])',
            re.IGNORECASE | re.MULTILINE
        )
        for match in dms_pattern.finditer(text):
            try:
                lat_deg = int(match.group("lat_deg"))
                lat_min = int(match.group("lat_min"))
                lat_sec = float(match.group("lat_sec"))
                lat_dir = match.group("lat_dir").upper()
                
                lon_deg = int(match.group("lon_deg"))
                lon_min = int(match.group("lon_min"))
                lon_sec = float(match.group("lon_sec"))
                lon_dir = match.group("lon_dir").upper()
                
                lat = self._dms_to_decimal(lat_deg, lat_min, lat_sec, lat_dir)
                lon = self._dms_to_decimal(lon_deg, lon_min, lon_sec, lon_dir)
                
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    continue
                    
                coord_key = (round(lat, 6), round(lon, 6))
                if coord_key in seen_coords:
                    continue
                seen_coords.add(coord_key)
                
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context_snippet = text[start:end].replace("\n", " ").strip()
                
                site_name = self._extract_site_name_from_context(context_snippet)
                
                results.append({
                    "latitude": lat,
                    "longitude": lon,
                    "context": context_snippet,
                    "site_name": site_name,
                })
            except (ValueError, AttributeError):
                continue
        
        # Pattern 3: Simple decimal pairs without direction indicators
        # "12.9716, 77.5946" or "Site center: 12.9716, 77.5946"
        simple_decimal = re.compile(
            r'(?P<lat>-?\d{1,2}\.\d{2,6})[,\s]+(?P<lon>-?\d{1,3}\.\d{2,6})',
            re.MULTILINE
        )
        for match in simple_decimal.finditer(text):
            try:
                lat = float(match.group("lat"))
                lon = float(match.group("lon"))
                
                # Basic sanity checks
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    continue
                    
                coord_key = (round(lat, 6), round(lon, 6))
                if coord_key in seen_coords:
                    continue
                seen_coords.add(coord_key)
                
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context_snippet = text[start:end].replace("\n", " ").strip()
                
                site_name = self._extract_site_name_from_context(context_snippet)
                
                results.append({
                    "latitude": lat,
                    "longitude": lon,
                    "context": context_snippet,
                    "site_name": site_name,
                })
            except ValueError:
                continue
        
        # Pattern 4: UTM coordinates (basic - note: UTM requires zone conversion)
        # "UTM Zone 43N 582639 4512345" - we'll extract but note it needs conversion
        utm_pattern = re.compile(
            r'UTM\s+Zone\s+(?P<zone>\d{1,2})(?P<hemisphere>[NS])\s+(?P<easting>\d{6,7})\s+(?P<northing>\d{7,8})',
            re.IGNORECASE | re.MULTILINE
        )
        for match in utm_pattern.finditer(text):
            # Note: UTM to lat/lon conversion requires pyproj library
            # For now, we'll log it but skip adding to results
            # Users can manually convert or we can add pyproj later
            logger.debug(f"Found UTM coordinates: {match.group(0)} (conversion not implemented)")
        
        logger.info(f"Extracted {len(results)} coordinate pairs from PDF")
        return results

    def extract_dates(self, context_window: int = 100) -> List[Dict]:
        """
        Extract year and year-range mentions for timeline visualisations.
        
        Recognises:
            - Modern ranges: "1998 to 2002", "1998-2002"
            - BCE/BC ranges: "2500–1900 BCE", "3000–2000 BC"
            - Single years: "summer 2005", "2004"
            - Contextual dates: "June–August 2014"
        
        Returns:
            List of dicts with keys: label, start_year, end_year, context, site_name (if found)
        """
        text = self._ensure_full_text()
        results: List[Dict] = []
        seen_ranges = set()  # Track ranges to avoid duplicates
        
        # Pattern 1: Modern year ranges (CE/AD)
        # "1998 to 2002", "1998-2002", "from 1998 to 2002"
        modern_range_pattern = re.compile(
            r'(?:from|between|during)?\s*(?P<start>(?:18|19|20)\d{2})\s*(?:to|-|–)\s*(?P<end>(?:18|19|20)\d{2})\b',
            re.IGNORECASE | re.MULTILINE
        )
        for match in modern_range_pattern.finditer(text):
            try:
                start_year = int(match.group("start"))
                end_year = int(match.group("end"))
                
                if start_year > end_year:
                    start_year, end_year = end_year, start_year
                
                range_key = (start_year, end_year)
                if range_key in seen_ranges:
                    continue
                seen_ranges.add(range_key)
                
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context_snippet = text[start:end].replace("\n", " ").strip()
                
                site_name = self._extract_site_name_from_context(context_snippet)
                
                results.append({
                    "label": f"{start_year}-{end_year}",
                    "start_year": start_year,
                    "end_year": end_year,
                    "context": context_snippet,
                    "site_name": site_name,
                })
            except (ValueError, AttributeError):
                continue
        
        # Pattern 2: BCE/BC date ranges
        # "2500–1900 BCE", "3000–2000 BC", "2500-1900 BCE"
        bce_range_pattern = re.compile(
            r'(?P<start>\d{3,4})\s*(?:-|–)\s*(?P<end>\d{3,4})\s*(?:BCE|BC|B\.C\.|B\.C\.E\.)',
            re.IGNORECASE | re.MULTILINE
        )
        for match in bce_range_pattern.finditer(text):
            try:
                start_year_bce = int(match.group("start"))
                end_year_bce = int(match.group("end"))
                
                if start_year_bce < end_year_bce:
                    start_year_bce, end_year_bce = end_year_bce, start_year_bce
                
                # Convert to negative years for timeline (BCE dates are negative)
                start_year = -start_year_bce
                end_year = -end_year_bce
                
                range_key = (start_year, end_year)
                if range_key in seen_ranges:
                    continue
                seen_ranges.add(range_key)
                
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context_snippet = text[start:end].replace("\n", " ").strip()
                
                site_name = self._extract_site_name_from_context(context_snippet)
                
                results.append({
                    "label": f"{start_year_bce}–{end_year_bce} BCE",
                    "start_year": start_year,
                    "end_year": end_year,
                    "context": context_snippet,
                    "site_name": site_name,
                })
            except (ValueError, AttributeError):
                continue
        
        # Pattern 3: Single BCE/BC years
        # "2500 BCE", "3000 BC"
        bce_single_pattern = re.compile(
            r'\b(?P<year>\d{3,4})\s*(?:BCE|BC|B\.C\.|B\.C\.E\.)\b',
            re.IGNORECASE | re.MULTILINE
        )
        for match in bce_single_pattern.finditer(text):
            try:
                year_bce = int(match.group("year"))
                year = -year_bce
                
                # Check if already in a range
                if any(r["start_year"] <= year <= r["end_year"] for r in results):
                    continue
                
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context_snippet = text[start:end].replace("\n", " ").strip()
                
                site_name = self._extract_site_name_from_context(context_snippet)
                
                results.append({
                    "label": f"{year_bce} BCE",
                    "start_year": year,
                    "end_year": year,
                    "context": context_snippet,
                    "site_name": site_name,
                })
            except (ValueError, AttributeError):
                continue
        
        # Pattern 4: Contextual modern dates with months/seasons
        # "summer 2005", "June–August 2014", "Field season: June–August 2014"
        contextual_date_pattern = re.compile(
            r'(?:summer|winter|spring|fall|autumn|field\s+season|excavated|surveyed|dated)\s+(?:in\s+)?(?P<year>(?:18|19|20)\d{2})\b',
            re.IGNORECASE | re.MULTILINE
        )
        for match in contextual_date_pattern.finditer(text):
            try:
                year = int(match.group("year"))
                
                # Skip if already captured in a range
                if any(r["start_year"] <= year <= r["end_year"] for r in results):
                    continue
                
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context_snippet = text[start:end].replace("\n", " ").strip()
                
                site_name = self._extract_site_name_from_context(context_snippet)
                
                results.append({
                    "label": str(year),
                    "start_year": year,
                    "end_year": year,
                    "context": context_snippet,
                    "site_name": site_name,
                })
            except (ValueError, AttributeError):
                continue
        
        # Pattern 5: Standalone modern years (18xx, 19xx, 20xx)
        # Avoid double-counting ones already captured
        year_pattern = re.compile(r'\b(?P<year>(?:18|19|20)\d{2})\b')
        for match in year_pattern.finditer(text):
            try:
                year = int(match.group("year"))
                
                # Skip if already in a range or contextual date
                if any(r["start_year"] <= year <= r["end_year"] for r in results):
                    continue
                
                # Skip if it's part of a UTM coordinate or other number
                context_check = text[max(0, match.start()-5):min(len(text), match.end()+5)]
                if re.search(r'UTM|Zone|\d{6,}', context_check):
                    continue
                
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context_snippet = text[start:end].replace("\n", " ").strip()
                
                site_name = self._extract_site_name_from_context(context_snippet)
                
                results.append({
                    "label": str(year),
                    "start_year": year,
                    "end_year": year,
                    "context": context_snippet,
                    "site_name": site_name,
                })
            except ValueError:
                continue
        
        logger.info(f"Extracted {len(results)} date mentions from PDF")
        return results
    
    def extract_sites(self) -> List[Dict]:
        """
        Extract archaeological site names and identifiers from the PDF.
        
        Recognises patterns like:
        - "Site 1: Mohenjo-daro"
        - "HST-202 (Hastinapur)"
        - "Trench T-5"
        - "Locus L12"
        - "Mound A at Site 3"
        
        Returns:
            List of dicts with keys: site_name, site_type, context
        """
        text = self._ensure_full_text()
        results: List[Dict] = []
        seen_sites = set()
        
        # Pattern 1: "Site X: Name" or "Site X Name"
        site_pattern1 = re.compile(
            r'Site\s+(?P<num>\d+)[:\s]+(?P<name>[A-Za-z][A-Za-z\s\-]+?)(?:[,\s\.]|$)',
            re.IGNORECASE | re.MULTILINE
        )
        for match in site_pattern1.finditer(text):
            site_name = f"Site {match.group('num')}: {match.group('name').strip()}"
            if site_name not in seen_sites:
                seen_sites.add(site_name)
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context_snippet = text[start:end].replace("\n", " ").strip()
                results.append({
                    "site_name": site_name,
                    "site_type": "Site",
                    "context": context_snippet,
                })
        
        # Pattern 2: "CODE-123 (Name)" or "CODE (Name)"
        site_pattern2 = re.compile(
            r'([A-Z]{2,4}[-]?\d{1,4})\s*\(([^)]+)\)',
            re.IGNORECASE | re.MULTILINE
        )
        for match in site_pattern2.finditer(text):
            site_name = f"{match.group(1)} ({match.group(2)})"
            if site_name not in seen_sites:
                seen_sites.add(site_name)
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context_snippet = text[start:end].replace("\n", " ").strip()
                results.append({
                    "site_name": site_name,
                    "site_type": "Site",
                    "context": context_snippet,
                })
        
        # Pattern 3: "Trench T-X" or "Locus LXX"
        for pattern_type, pattern in [
            ("Trench", re.compile(r'Trench\s+([A-Z]?[-]?\d+)', re.IGNORECASE | re.MULTILINE)),
            ("Locus", re.compile(r'Locus\s+([A-Z]?[-]?\d+)', re.IGNORECASE | re.MULTILINE)),
            ("Mound", re.compile(r'Mound\s+([A-Z])\s+at\s+Site\s+(\d+)', re.IGNORECASE | re.MULTILINE)),
        ]:
            for match in pattern.finditer(text):
                if pattern_type == "Mound":
                    site_name = f"Mound {match.group(1)} at Site {match.group(2)}"
                else:
                    site_name = f"{pattern_type} {match.group(1)}"
                
                if site_name not in seen_sites:
                    seen_sites.add(site_name)
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context_snippet = text[start:end].replace("\n", " ").strip()
                    results.append({
                        "site_name": site_name,
                        "site_type": pattern_type,
                        "context": context_snippet,
                    })
        
        logger.info(f"Extracted {len(results)} site names from PDF")
        return results
    
    def _extract_site_name_from_context(self, context: str) -> str:
        """
        Try to extract site name from context snippet.
        
        Looks for patterns like:
        - "Site 1: Mohenjo-daro"
        - "HST-202 (Hastinapur)"
        - "Trench T-5"
        - "Locus L12"
        - "Mound A at Site 3"
        """
        # Pattern 1: "Site X: Name" or "Site X Name"
        site_pattern1 = re.compile(r'Site\s+(?P<num>\d+)[:\s]+(?P<name>[A-Za-z][A-Za-z\s\-]+?)(?:[,\s]|$)', re.IGNORECASE)
        match = site_pattern1.search(context)
        if match:
            return f"Site {match.group('num')}: {match.group('name').strip()}"
        
        # Pattern 2: "CODE-123 (Name)" or "CODE (Name)"
        site_pattern2 = re.compile(r'([A-Z]{2,4}[-]?\d{1,4})\s*\(([^)]+)\)', re.IGNORECASE)
        match = site_pattern2.search(context)
        if match:
            return f"{match.group(1)} ({match.group(2)})"
        
        # Pattern 3: "Trench T-X" or "Locus LXX"
        site_pattern3 = re.compile(r'(Trench|Locus|Mound)\s+([A-Z]?[-]?\d+)', re.IGNORECASE)
        match = site_pattern3.search(context)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        # Pattern 4: "Mound X at Site Y"
        site_pattern4 = re.compile(r'Mound\s+([A-Z])\s+at\s+Site\s+(\d+)', re.IGNORECASE)
        match = site_pattern4.search(context)
        if match:
            return f"Mound {match.group(1)} at Site {match.group(2)}"
        
        return None

