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

### Step 2: Set Up API Key
Create a `.env` file in the `archaeological-rag-chatbot` directory:
```
OPENAI_API_KEY=sk-your-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

Alternative for public deployment:
- Users can enter their own OpenAI API key directly in the app sidebar.
- The key is stored only in their active browser session.

### Step 3: Process the PDF (Optional but Recommended)
```bash
python setup.py
```
This will:
- Extract text from the PDF
- Create vector embeddings
- Build the searchable vector store

**Note:** This step takes 5-10 minutes depending on PDF size.

### Step 4: Run the Chatbot
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

### Step 5: Start Chatting!
- If you ran `setup.py`, click "Load Existing Vector Store" in the sidebar
- Or upload and process the PDF through the web interface
- In the sidebar, paste your OpenAI API key and click "Apply key" (if you did not set `.env`)
- Ask questions about archaeological surveys!

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
- Make sure the PDF file exists at `../archelogical pdf pr0ooject.pdf`
- Try uploading the PDF through the web interface instead

### Vector Store Not Found
- Run `python setup.py` to create the vector store
- Or process the PDF through the web interface

## 💡 Tips

- The first run (processing PDF) takes time - be patient!
- Once the vector store is created, subsequent runs are instant
- You can ask follow-up questions - the chat history is maintained
- Click "View Sources" to see where answers came from

