# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
# Activate your virtual environment
# Windows:
..\venv\Scripts\activate
# macOS/Linux:
source ../venv/bin/activate

# Install packages
pip install -r requirements.txt
```

EasyOCR is included in `requirements.txt` with CPU-only PyTorch for Cloud-friendly installs.
For local GPU acceleration, see `requirements-dev.txt`.

### Step 2: Set Up Hosted API Keys
Create a `.env` file in the `archaeological-rag-chatbot` directory:
```
JINA_API_KEY=jina_...
GEMINI_API_KEY_1=AIza...
GEMINI_API_KEY_2=AIza...
GEMINI_API_KEY_3=AIza...
```

- Jina key: https://jina.ai/api-dashboard/key-manager
- Gemini keys: https://aistudio.google.com/app/apikey (one per Google account for rotation)

Optional for unlimited personal use:
- Paste your OpenAI key in the sidebar under **Use my own OpenAI API key**.

### Step 3: Process the PDF (Optional but Recommended)
```bash
python setup.py
```
This will:
- Extract text from the PDF
- Create vector embeddings
- Build the searchable vector store

**Note:** This step takes a few minutes depending on PDF size.

### Step 4: Run the Chatbot
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

### Step 5: Start Chatting!
- If you ran `setup.py`, click "Continue from last session" in the Chat & Analysis page
- Or upload and process the PDF in the Chat & Analysis page
- Free plan works without pasting any key
- Optional: open **Use my own OpenAI API key** in the sidebar for unlimited use
- Ask questions about archaeological surveys!

## 🌍 Deploy Publicly in Minutes (Recommended)

Use **Streamlit Community Cloud** for the fastest deployment.

1. Push your project to GitHub
2. Open https://share.streamlit.io
3. Click **New app** and connect your repo
4. Set entry file to `app.py`
5. Deploy and share the public URL

Add hosted keys in Streamlit app settings > **Secrets**:

```toml
JINA_API_KEY = "jina_..."
GEMINI_API_KEY_1 = "AIza..."
GEMINI_API_KEY_2 = "AIza..."
GEMINI_API_KEY_3 = "AIza..."
```

Optional Europeana lookup key:

```toml
EUROPEANA_API_KEY = "your-europeana-key"
```

Notes for Community Cloud:
- Do not commit `vector_store/` or populated `user_data/`
- The app can start without a prebuilt vector index
- OpenCV uses the headless package for leaner deploys
- `packages.txt` intentionally keeps a minimal Linux package list for Streamlit Cloud compatibility
- Prefer Python 3.11 in Streamlit Cloud advanced settings when available
- EasyOCR models download once per session; the photo organizer shows progress while scanning
- OCR is skipped when filenames already include trench, locus, artifact type, and context
- If `easyocr` is not installed, hotspot-based manual review still works

## 📝 Example Questions to Try

- "What are the key steps in conducting an archaeological survey?"
- "How do I identify potential archaeological sites?"
- "What equipment is needed for field surveys?"
- "What are the documentation requirements for archaeological findings?"
- "Explain the methodology for site mapping."

## ⚠️ Troubleshooting

### "Hosted AI keys are not configured"
- Make sure `.env` contains `JINA_API_KEY` and at least one `GEMINI_API_KEY_*`
- On Streamlit Cloud, add the same keys in app **Secrets**

### PDF Processing Fails
- Try uploading the PDF again from the Chat & Analysis page
- Make sure the PDF is not password-protected or corrupted
- Free plan supports PDFs up to 50 pages

### Streamlit Cloud dependency install fails
- If deployment stops during the apt step, keep `packages.txt` minimal and avoid adding distro-specific packages like `libglib2.0-0`
- Redeploy after pushing the updated `packages.txt`; Streamlit Cloud will reinstall system packages from scratch

### Vector Store Not Found
- Run `python setup.py` to create the vector store
- Or process the PDF through the web interface

## 💡 Tips

- The first run (processing PDF) takes time - be patient!
- Once the vector store is created, subsequent runs are instant
- You can ask follow-up questions - the chat history is maintained
- Click "View Sources" to see where answers came from
- Free plan: 20 questions and 1 PDF index per session
