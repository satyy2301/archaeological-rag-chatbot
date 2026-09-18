# 🏛️ Archaeological Survey RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot for archaeological survey questions. This system processes PDF documents about archaeological surveys and provides intelligent answers based on the document content.

LIVE LINK : https://archyrag.streamlit.app/
## Features

- 📄 **PDF Processing**: Extracts and processes text from archaeological survey PDFs
- 🔍 **Semantic Search**: Uses vector embeddings for intelligent document retrieval
- 💬 **Interactive Chat**: Streamlit-based web interface for easy interaction
- 🧠 **RAG Architecture**: Combines retrieval and generation for accurate, context-aware answers
- 📚 **Source Citation**: Shows source documents for transparency
- 🆓 **Free Plan**: Works out of the box with hosted Jina embeddings and Gemini chat (session limits apply)
- 🔑 **Bring Your Own OpenAI Key**: Optional sidebar key for unlimited use (kept only for the current browser session)
- 🖼️ **Artifact Image Analysis**: Upload photos of inscriptions/coins/manuscripts for non-destructive enhancement (denoise, shadow removal, CLAHE, Retinex, sharpening), OCR with bounding boxes and confidence, region zoom, and feedback-saving for future improvements
- 🌐 **Similar Finds Lookup**: Searches lightweight public collection APIs for comparable objects without bundling bulky local reference datasets

## 📸 Screenshots

### Chat Interface
![Chat Interface](images/Screenshot%202025-12-31%20204640.png)

### Map & Timeline View  
![Map View](images/Screenshot%202025-12-31%20204659.png)
## Installation

1. **Navigate to the project directory:**
   ```bash
   cd archaeological-rag-chatbot
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
   
   Or use the existing virtual environment in the parent directory:
   ```bash
   # On Windows:
   ..\venv\Scripts\activate
   # On macOS/Linux:
   source ../venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (for local dev / deployment owner):**
   - Create a `.env` file in the `archaeological-rag-chatbot` directory
   - Add hosted free-tier keys:
     ```
     JINA_API_KEY=jina_...
     GEMINI_API_KEY_1=AIza...
     GEMINI_API_KEY_2=AIza...
     GEMINI_API_KEY_3=AIza...
     ```
   - Visitors can optionally paste their own OpenAI key in the sidebar for unlimited use

5. **Optional: Pre-process the PDF (recommended for faster startup):**
   ```bash
   python setup.py
   ```
   This will process the PDF and create the vector store before running the app.

## Usage

1. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser:**
   - The app will automatically open at `http://localhost:8501`
   - Or manually navigate to the URL shown in the terminal

3. **Process your PDF (if not pre-processed):**
   - Open the **Chat & Analysis** tab and upload your archaeological survey PDF
   - Click **Process Document & Start Chatting**
   - Wait for the system to process the document (this may take a few minutes)
   - **Note:** If you ran `setup.py`, the vector store is already created and you can click **Continue from last session**

4. **Start chatting:**
   - Once processed, you can ask questions about archaeological surveys
   - The chatbot will provide answers based on the PDF content
   - View source citations to see where the information came from
   - Optional: open **Use my own OpenAI API key** in the sidebar for unlimited use

### Image Analysis (Found Something?)
- Open the "Found Something?" tab
- Upload a high-resolution photo (JPEG/PNG/TIFF)
- Optionally add context (artifact type, material, size, location, markings, script profile)
- Click "Assess Artifact" to see:
   - Side-by-side enhanced images (CLAHE, Retinex, Sharpen)
   - Preprocessing previews (denoise, shadow reduction, normalization)
   - Detected regions with OCR text, confidence, suggested readings, and backend notes
   - Similar finds from public collection sources such as The Met and Wikidata, with optional Europeana results if `EUROPEANA_API_KEY` is configured
   - Interactive zoom of any numbered region and a field to save your transcription corrections to `user_data/corrections.json`

## Deployment Notes

- Do not commit `vector_store/`, uploaded files, or runtime `user_data/` to the repository.
- The app is open-access by default with no login required.
- OCR is lightweight by default. If `easyocr` is not installed, the app falls back to hotspot detection so the review UI still works.
- Build the FAISS index at runtime from an uploaded PDF, or host a generated index outside the repo if you need a prebuilt corpus.

## Project Structure

```
archaeological-rag-chatbot/
├── app.py                 # Streamlit web application
├── pdf_processor.py       # PDF text extraction and chunking
├── vector_store.py        # Provider-aware embeddings and FAISS storage
├── rag_chain.py          # RAG chain implementation (Gemini hosted or OpenAI BYOK)
├── config/               # Provider, secrets, and rate-limit helpers
├── embeddings/           # Jina v3 embedding integration
├── llm/                  # Gemini key-rotation helper
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── README.md            # This file
├── image_analyzer.py     # Image preprocessing, enhancement, OCR, overlays
├── artifact_lookup.py    # Lightweight external collection lookup
└── vector_store/         # Generated locally or at runtime, not committed
```

## How It Works

1. **PDF Processing**: The PDF is processed to extract text, which is then split into manageable chunks
2. **Embedding Creation**: Text chunks are converted to vector embeddings using Jina (free plan) or OpenAI (BYOK)
3. **Vector Store**: Embeddings are stored in a FAISS vector database for fast similarity search
4. **Query Processing**: When you ask a question:
   - The question is converted to an embedding
   - Similar document chunks are retrieved from the vector store
   - The retrieved context is passed to Gemini (free plan) or GPT-3.5-turbo (BYOK) along with your question
   - The LLM generates an answer based on the retrieved context

## Example Questions

- "What are the key steps in conducting an archaeological survey?"
- "How do I identify potential archaeological sites?"
- "What equipment is needed for field surveys?"
- "What are the documentation requirements for archaeological findings?"
- "Explain the methodology for site mapping."

## Configuration

You can modify the following in the code:

- **Chunk Size**: Adjust `chunk_size` in `pdf_processor.py` (default: 1000 characters)
- **Embedding Model**: See `config/providers.py` (Jina `jina-embeddings-v3` or OpenAI `text-embedding-3-small`)
- **LLM Model**: See `config/providers.py` (Gemini `gemini-3.6-flash` or OpenAI `gpt-3.5-turbo`)
- **Temperature**: Adjust `temperature` for more/less creative responses (default: 0.7)

## Public Deployment (Fastest and Easiest)

The smoothest public deployment for this project is **Streamlit Community Cloud**.

### Why this is the quickest option
- Native support for Streamlit apps
- Free public URL in minutes
- No server setup or Docker required
- Easy redeploy on every GitHub push

### Steps
1. Push this repository to GitHub.
2. Go to Streamlit Community Cloud: https://share.streamlit.io
3. Click **New app** and select this repository/branch.
4. Set the main file path to `app.py`.
5. Click **Deploy**.

This repo includes deployment helpers:
- `packages.txt` for required Linux system libraries used by OpenCV/EasyOCR
- `.streamlit/config.toml` for Streamlit runtime settings
- `.streamlit/secrets.toml.example` for optional fallback secret format
- `deploy_utils.py` for cloud-aware runtime behavior
- CPU-only `torch`/`torchvision` pins in `requirements.txt` (avoids CUDA wheels on Cloud)

For Streamlit Community Cloud, keep `packages.txt` minimal. Avoid pinning distro-specific libraries that may not exist on Streamlit's current base image.

### Cloud performance notes
- Use **Python 3.11** in Streamlit Cloud advanced settings when available (more stable than bleeding-edge runtimes).
- EasyOCR models download once per session on first photo with text reading enabled (~30–60 seconds).
- Photo organizer skips OCR when filename metadata already includes trench, locus, artifact type, and context.
- The `vector_store/` folder is ephemeral on Cloud; upload and index your PDF each session unless you add external storage.
- For local GPU development, see `requirements-dev.txt` for optional CUDA torch install notes.

### Hosted API Keys (Server-Side)
Set these in Streamlit Cloud **Secrets** (or local `.env`) so visitors can use the free plan without pasting keys:

```toml
JINA_API_KEY = "jina_..."
GEMINI_API_KEY_1 = "AIza..."
GEMINI_API_KEY_2 = "AIza..."
GEMINI_API_KEY_3 = "AIza..."
```

### Optional BYOK (User OpenAI Key)
- Users can open **Use my own OpenAI API key** in the sidebar.
- Enter a key with **Apply key**.
- The key is not stored in `user_data` files or repository.

Optional lookup secret:

```toml
EUROPEANA_API_KEY = "your-europeana-key"
```

Without this key, the app still uses public sources that do not require authentication.

## Troubleshooting

### "Hosted AI keys are not configured"
- For local development, set `JINA_API_KEY` and `GEMINI_API_KEY_1/2/3` in `.env`.
- On Streamlit Cloud, add the same keys in app **Secrets**.
- Users can also paste their own OpenAI key under **Use my own OpenAI API key**.

### PDF Processing Errors
- Try a different PDF if the current one fails to process
- Some PDFs with complex layouts may require manual text extraction

### Streamlit Cloud dependency install errors
- If the build fails while processing `packages.txt`, remove nonessential or distro-specific apt packages and redeploy
- This repository intentionally uses a minimal `packages.txt` to stay compatible with Streamlit Community Cloud's Linux image
- `requirements.txt` pins CPU-only PyTorch wheels to keep install size and memory use lower on Cloud

### App restarts or health check failures during PDF indexing
- Large PDFs are indexed in batches to reduce memory spikes
- If the app still restarts, try a smaller PDF first or wait for indexing to finish before using photo OCR in the same session

### Vector Store Issues
- Delete the `vector_store/` directory and reprocess the PDF
- Make sure you have write permissions in the project directory

## Dependencies

- **streamlit**: Web interface
- **langchain**: RAG framework
- **langchain-openai**: OpenAI integration
- **pdfplumber/pypdf2**: PDF processing
- **faiss-cpu**: Vector similarity search
- **langchain-openai**: OpenAI chat and embedding integration
- **openai**: OpenAI API client

## License

This project is provided as-is for educational and research purposes.

## Contributing

Feel free to submit issues or pull requests to improve the chatbot!

