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

Optional OCR upgrade for local use:
```bash
pip install easyocr
```

### Step 2: Set Up API Key
Create a `.env` file in the `archaeological-rag-chatbot` directory:
```
OPENAI_API_KEY=sk-your-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

Alternative for public deployment:
- Enter an OpenAI API key directly in the app sidebar.
- The key is stored only in the active browser session.

### Step 3: Process the PDF (Optional but Recommended)
```bash
python setup.py
```
This will:
- Extract text from the PDF
- Create vector embeddings
- Build the searchable vector store

**Note:** This step takes 5-10 minutes depending on PDF size.

### Step 4: Run the Research Lab
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` with the **landing page**.

### Step 5: Enter the Lab
1. Click **Enter Research Lab** on the landing page (or bookmark `/Research_Lab` for direct access)
2. Paste your OpenAI API key in the sidebar and click **Apply key** (if you did not set `.env`)
3. Follow the onboarding wizard: API key → upload PDF → choose a station
4. If you ran `setup.py`, click **Continue from last session** at the Document Intelligence Desk
5. Navigate between lab stations using the sidebar and start researching!

## 🌍 Deploy Publicly in Minutes (Recommended)

Use **Streamlit Community Cloud** for the fastest deployment.

1. Push your project to GitHub
2. Open https://share.streamlit.io
3. Click **New app** and connect your repo
4. Set entry file to `app.py`
5. Deploy and share the public URL

Optional fallback key for visitors:
- In Streamlit app settings, add secret:

```toml
OPENAI_API_KEY = "sk-..."
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
- If `easyocr` is not installed, hotspot-based manual review still works

## 📝 Example Questions to Try

- "What are the key steps in conducting an archaeological survey?"
- "How do I identify potential archaeological sites?"
- "What equipment is needed for field surveys?"
- "What are the documentation requirements for archaeological findings?"
- "Explain the methodology for site mapping."

## ⚠️ Troubleshooting

### "OPENAI_API_KEY not found"
- Make sure `.env` file exists in the `archaeological-rag-chatbot` directory
- Check that the API key is correctly formatted (starts with `sk-`)

### PDF Processing Fails
- Try uploading the PDF again from the Document Intelligence Desk
- Make sure the PDF is not password-protected or corrupted

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

