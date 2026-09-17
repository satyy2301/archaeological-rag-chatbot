"""User-facing copy for the Streamlit app — plain English, short sentences."""

COPY = {
    "sidebar": {
        "api_key_header": "OpenAI API Key",
        "api_key_caption": "Paste your OpenAI API key for this browser session.",
        "api_key_label": "Your OpenAI API Key",
        "api_key_placeholder": "sk-...",
        "api_key_help": "Your key stays in this session only. It is cleared when you click Clear key or close the browser.",
        "apply_key_saved": "Key saved for this session. Prepare a document to start chatting.",
        "clear_key_info": "Session key cleared.",
        "document_loaded": "loaded",
        "load_different_document": "Load a different document",
        "assistant_mode_header": "Assistant Mode",
        "assistant_mode_label": "What are you working on?",
        "assistant_mode_help": "Pick a focus area so answers match your task.",
        "api_key_tip": "Tip: Paste your API key above. For local use, you can also add it to a `.env` file.",
        "quick_starter_header": "Quick Starter Questions",
    },
    "chat": {
        "subheader": "Ask questions, explore sites, plan surveys, and check rules using your own archaeological documents.",
        "active_mode": "Active mode:",
        "view_sources": "View Sources & Locations",
        "welcome_title": "Welcome to the Archaeological Survey Assistant",
        "welcome_body": (
            "Upload a PDF — a survey report, excavation notes, or research paper — "
            "and ask questions in plain English. No technical knowledge needed."
        ),
        "step1_title": "Step 1 — Upload your document",
        "api_key_warning": (
            "Add your OpenAI API key first — paste it in the sidebar on the left, "
            "then upload your document here."
        ),
        "pdf_uploader_label": "Choose a PDF file (up to 200 MB)",
        "pdf_uploader_help": "Your file is only used in this session. It is not stored permanently.",
        "pdf_ready": "is ready to process",
        "process_button": "Prepare document and start chat",
        "resume_prompt": "Already prepared a document before? Continue your session:",
        "resume_button": "Continue from last session",
        "resume_error": "Could not reload the previous session. Please upload a new document.",
        "what_can_i_ask_title": "What can I ask?",
        "what_can_i_ask_body": """
Once your document is ready, try asking:

- *"What is this document about?"*
- *"Which archaeological sites are mentioned?"*
- *"What survey methods were used?"*
- *"Summarise the main findings."*
- *"What permits or laws are discussed?"*
- *"Explain soil layers in simple terms."*
""",
        "api_key_help_title": "Need an API key?",
        "api_key_help_body": (
            "Get one at [platform.openai.com](https://platform.openai.com) "
            "→ paste it in the **OpenAI API Key** field in the sidebar."
        ),
    },
    "maps": {
        "map_title": "Interactive Site Map",
        "map_caption": (
            "If your PDF includes map coordinates, the map fills in automatically. "
            "You can also upload a CSV with columns: site_name, latitude, longitude, and optional period."
        ),
        "map_from_pdf": "Found in your PDF:",
        "map_coords_expander": "View site coordinates",
        "map_csv_label": "Optional: upload a site list (CSV)",
        "map_csv_from_upload": "From your uploaded CSV:",
        "map_csv_table_expander": "View uploaded site table",
        "map_csv_error": "The CSV needs at least these columns: {required}. Found: {found}",
        "timeline_title": "Timeline of Excavations / Surveys",
        "timeline_caption": (
            "If your PDF mentions years or date ranges, a simple timeline is built automatically. "
            "You can also upload a CSV with site_name, start_year, and optional end_year."
        ),
        "timeline_from_pdf": "Found in your PDF (grouped by context):",
        "timeline_chart_error": "Could not show the timeline chart: {error}",
        "timeline_csv_label": "Optional: upload a timeline CSV",
        "timeline_no_valid_rows": "No valid year rows were found after reading the file.",
        "timeline_csv_error": "The timeline CSV needs at least site_name and start_year columns.",
        "graph_title": "Simple Knowledge Graph (Sites ↔ Periods)",
        "graph_caption": "Use your site and timeline data to think about how places, periods, and regions connect.",
        "sites_from_pdf": "Sites found in your PDF:",
        "sites_count": "Found {count} site(s) in the document",
        "graph_body": """
This view helps you think about **connections**:
- Sites linked to **time periods** and **regions**
- Finds linked to **dig contexts** and **soil layers**

For a full interactive graph, you can export your site table to tools like Neo4j or Gephi.
""",
    },
    "docs_glossary": {
        "viewer_title": "Document & Source Viewer",
        "viewer_caption": (
            "When the assistant answers from your PDF, open **Sources** in the chat tab "
            "to see the exact passages and page numbers used."
        ),
        "recent_pdf": "Most recent uploaded PDF: **{name}**",
        "highlighting_tip": """
**How to find where an answer came from:**
1. Open the **Chat** tab and expand *"View Sources & Locations"* under a message.
2. Read the quoted text and note the page number if shown.
3. Open your PDF at that page to see the full passage.
""",
        "glossary_title": "Archaeological Terms — Plain English",
        "glossary_lookup": "Look up a term:",
        "glossary_full": "Show full glossary",
        "glossary": {
            "Context": "One layer or event in a dig that archaeologists record as a single unit.",
            "Stratigraphy": "The order of soil layers in the ground, from oldest to newest.",
            "Feature": "Something built or dug into the ground that stays in place, like a wall, pit, or hearth.",
            "Assemblage": "A group of finds discovered together in the same context, thought to be related.",
            "Phase": "A group of contexts from the same broad period of activity at a site.",
            "Datum": "A fixed survey point used to measure heights and positions on site.",
            "Transect": "A set walking line used during field survey to record finds systematically.",
        },
    },
    "compliance": {
        "title": "Regulatory & Compliance Helper",
        "caption": (
            "These tools use your documents and general archaeological knowledge. "
            "Always check current local laws and official guidance."
        ),
        "permit_label": "Describe your project and location",
        "permit_placeholder": "e.g. field survey near a river in [your region], with planned test pits...",
        "permit_button": "Create permit checklist",
        "report_label": "Reporting and compliance details",
        "report_placeholder": "Summarise your project, methods, and main findings...",
        "report_button": "Draft report outline",
        "methodology_title": "Survey Methodology Template",
        "methodology_label": "Survey details (setting, aims, limits)",
        "methodology_placeholder": "e.g. walkover survey across 5 km² of farmland...",
        "methodology_button": "Create methodology template",
        "report_generator_title": "Report Generator",
        "report_type_label": "Report type",
        "project_name_label": "Project name",
        "project_name_default": "Archaeological Investigation",
        "location_label": "Location",
        "generate_report_button": "Generate report",
        "export_report_button": "Export report",
        "download_report_button": "Download report",
        "report_preview_title": "Report preview",
        "citation_title": "Citation Generator",
        "citation_label": "Book or article details (author, year, title, publisher, etc.)",
        "citation_placeholder": "e.g. Renfrew, C. and Bahn, P. 2016. Archaeology: Theories, Methods and Practice. London: Thames & Hudson.",
        "citation_style_label": "Citation style",
        "citation_button": "Format citation",
        "spinner_permits": "Checking likely permits and legal steps...",
        "spinner_report": "Drafting a report outline...",
        "spinner_methodology": "Building a methodology template...",
        "spinner_generating_report": "Generating report...",
        "spinner_citation": "Formatting citation...",
    },
    "photo_organizer": {
        "title": "Dig Photo Organizer",
        "intro": (
            "Upload dig photos or point to a folder. The app sorts them by trench, dig area (locus), "
            "find type, soil layer, and date. You can also make field reports and spot duplicate photos."
        ),
        "analyze_checkbox": "Read signs and labels in photos",
        "analyze_help": (
            "Looks for trench numbers, locus numbers, object type, and other notes "
            "on chalkboards, field forms, and finds."
        ),
        "scan_option_title": "Option 1: Scan a folder",
        "scan_path_label": "Folder path on your computer:",
        "scan_path_placeholder": "C:/path/to/photos or ./photos",
        "scan_path_help": "Enter the full path to a folder that contains your photos.",
        "scan_button": "Scan folder",
        "upload_option_title": "Option 2: Upload photos",
        "upload_label": "Upload photos",
        "upload_help": "Select one or more photos to organise.",
        "spinner_reading": "Reading photos...",
        "spinner_ocr_first_run": (
            "Loading text-reading models for the first time. This can take about a minute, "
            "then later photos are much faster."
        ),
        "progress_photo": "Photo {current} of {total}: {filename}",
        "scan_success": "Found {count} photos!",
        "upload_success": "Processed {count} photos!",
        "ocr_limited_warning": (
            "Text reading is limited on this install. Install the `easyocr` package "
            "for better reading of chalkboards and field forms."
        ),
        "ocr_cloud_note": (
            "Text reading uses EasyOCR. The first photo in a session downloads models once; "
            "after that, results are cached for the rest of the session."
        ),
        "organize_title": "Organise photos",
        "organize_label": "Sort by:",
        "detection_details": "How details were found",
        "no_details": "No details were detected in this photo.",
        "sources_label": "Found using:",
        "reports_title": "Reports & analysis",
        "field_report_button": "Create field report",
        "field_report_area_label": "Field report",
        "download_report_button": "Download report",
        "duplicates_button": "Find duplicate photos",
        "duplicates_found": "Found {count} possible duplicate groups",
        "duplicate_group": "Duplicate group {index}",
        "no_duplicates": "No duplicates found!",
        "statistics_expander": "Summary statistics",
    },
    "found_something": {
        "title": "Found Something?",
        "intro": (
            "Upload a photo or describe what you found. Get a plain-English assessment, "
            "identification help, and practical next steps."
        ),
        "input_method_label": "How would you like to share your find?",
        "photo_option_title": "Option A: Upload a photo",
        "photo_uploader_label": "Upload a photo of your find",
        "photo_uploader_help": "Use a clear, well-lit photo if you can.",
        "uploaded_caption": "Your uploaded photo",
        "context_expander": "Add extra details (optional)",
        "script_profile_label": "Writing / inscription type",
        "script_profile_help": (
            "Choose the script you expect on the object. If unsure, leave Auto. "
            "The app will still enhance the image for manual review."
        ),
        "assess_button": "Assess find",
        "spinner_photo": "Looking at your photo...",
        "spinner_text": "Reviewing your description...",
        "results_title": "Assessment results",
        "full_assessment_expander": "Read full detailed assessment",
        "source_snippets": "Source passages",
        "enhancement_title": "Enhanced image views",
        "enh_clahe": "Stronger contrast",
        "enh_clahe_caption": "Contrast improved",
        "enh_retinex": "Even lighting",
        "enh_retinex_caption": "Lighting balanced",
        "enh_sharpen": "Sharper edges",
        "enh_sharpen_caption": "Edges highlighted",
        "preprocessing_expander": "Show image cleanup steps",
        "pre_denoised": "Noise reduced",
        "pre_shadow": "Shadows reduced",
        "pre_normalized": "Colours balanced",
        "similar_finds_title": "Similar finds in public collections",
        "similar_finds_caption": "These are rough matches from public museums. Some may not be related to your find.",
        "no_similar_finds": "No close matches were found in public collections from this photo.",
        "recommendations_title": "What to do next",
        "technical_expander": "Technical details (advanced)",
        "technical_payload": "Image analysis data",
        "detected_regions": "Marked text areas",
        "detected_regions_caption": "Numbered areas on the image",
        "detected_text_summary": "Clearest text found: {text}",
        "text_reader_note": "Text reader used: {backend}",
        "zoom_region_label": "Zoom area number",
        "suggested_readings": "Possible readings",
        "correction_label": "Your reading for this area",
        "save_correction_button": "Save correction",
        "correction_saved": "Thank you — your correction was saved.",
        "text_option_title": "Option B: Describe in words",
        "text_option_caption": "Answer a few short questions about what you found.",
        "markings_help": "Describe any marks, writing, or decoration you can see.",
        "your_description": "Your description",
        "detailed_assessment": "Detailed assessment",
        "view_sources": "View sources",
        "recommendations": "Recommendations",
        "no_summary": "No summary is available for this image yet.",
    },
    "status": {
        "assistant_ready": "Assistant is ready — start chatting below!",
        "key_saved_prepare": "Key saved for this session. Prepare a document to start chatting.",
        "document_loaded_name": "Document loaded",
        "reading_document": "Reading your document...",
        "indexing_document": "Preparing your document for chat (this may take a minute)...",
        "document_read_sections": "Document read — found {count} sections of text.",
        "document_prepared": "Document prepared successfully!",
        "setting_up_assistant": "Setting up your assistant...",
        "auto_extracted": "Found in your PDF: {summary}",
        "pdf_ready_named": "**{name}** is ready to process",
    },
    "errors": {
        "no_document_indexed": "No document is ready yet. Please upload and prepare a PDF first.",
        "assistant_init": "Could not start the assistant: {error}",
        "api_key_invalid": (
            "Please add a valid OpenAI API key in the sidebar. "
            "For local use, you can also add it to a `.env` file."
        ),
        "no_pdf_text": "No text could be read from this PDF. Try a different file or a text-based PDF.",
        "pdf_processing": "Could not prepare this PDF: {error}",
        "need_pdf_first": "Please upload and prepare a PDF first. The assistant needs your document before it can answer.",
        "scan_directory": "Could not scan folder: {error}",
        "process_photos": "Could not process photos: {error}",
    },
}
