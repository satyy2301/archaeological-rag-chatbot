# 🏛️ Archaeological Survey RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot for archaeological survey questions. This system processes PDF documents about archaeological surveys and provides intelligent answers based on the document content.

LIVE LINK : https://archyrag.streamlit.app/
## Features

- 📄 **PDF Processing**: Extracts and processes text from archaeological survey PDFs
- 🔍 **Semantic Search**: Uses vector embeddings for intelligent document retrieval
- 💬 **Interactive Chat**: Streamlit-based web interface for easy interaction
- 🧠 **RAG Architecture**: Combines retrieval and generation for accurate, context-aware answers
- 📚 **Source Citation**: Shows source documents for transparency
- 🔑 **Bring Your Own OpenAI Key**: Paste an OpenAI API key in the sidebar (kept only for the current browser session)
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

4. **Set up environment variables:**
   - Create a `.env` file in the `archaeological-rag-chatbot` directory
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```
   - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

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
   - Paste your OpenAI API key in the sidebar under **OpenAI API Key**

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
├── vector_store.py        # OpenAI embeddings and FAISS storage
├── rag_chain.py          # RAG chain implementation
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── README.md            # This file
├── image_analyzer.py     # Image preprocessing, enhancement, OCR, overlays
├── artifact_lookup.py    # Lightweight external collection lookup
└── vector_store/         # Generated locally or at runtime, not committed
```

## How It Works

1. **PDF Processing**: The PDF is processed to extract text, which is then split into manageable chunks
2. **Embedding Creation**: Text chunks are converted to vector embeddings using OpenAI embeddings
3. **Vector Store**: Embeddings are stored in a FAISS vector database for fast similarity search
4. **Query Processing**: When you ask a question:
   - The question is converted to an embedding
   - Similar document chunks are retrieved from the vector store
   - The retrieved context is passed to an LLM (GPT-3.5-turbo) along with your question
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
- **Embedding Model**: Change `embedding_model` in `vector_store.py` (default: "text-embedding-3-small")
- **LLM Model**: Modify `model_name` in `rag_chain.py` (default: "gpt-3.5-turbo")
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

For Streamlit Community Cloud, keep `packages.txt` minimal. Avoid pinning distro-specific libraries that may not exist on Streamlit's current base image.

### API Key Entry
- The app supports session-level key entry in the sidebar.
- Enter a key with **Apply key**.
- The key is not stored in `user_data` files or repository.

### Optional Owner Key Fallback
If you want the app to also work without manually entered keys, set a default secret in Streamlit Cloud:
- In app settings > **Secrets**, add:

```toml
OPENAI_API_KEY = "sk-..."
```

This acts as a fallback when a visitor does not provide a key.

Optional lookup secret:

```toml
EUROPEANA_API_KEY = "your-europeana-key"
```

Without this key, the app still uses public sources that do not require authentication.

## Troubleshooting

### "OPENAI_API_KEY not found"
- For local development, make sure you've created a `.env` file with your OpenAI API key.
- For public usage, you can paste a key in the sidebar under **OpenAI API Key**.
- On Streamlit Cloud, you can also set `OPENAI_API_KEY` in app secrets as fallback.

### PDF Processing Errors
- Try a different PDF if the current one fails to process
- Some PDFs with complex layouts may require manual text extraction

### Streamlit Cloud dependency install errors
- If the build fails while processing `packages.txt`, remove nonessential or distro-specific apt packages and redeploy
- This repository intentionally uses a minimal `packages.txt` to stay compatible with Streamlit Community Cloud's Linux image

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

