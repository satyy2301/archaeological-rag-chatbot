# 🏛️ Archaeological Survey RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot designed to help users with archaeological survey questions. This system processes PDF documents about archaeological surveys and provides intelligent answers based on the document content.

## Features

- 📄 **PDF Processing**: Extracts and processes text from archaeological survey PDFs
- 🔍 **Semantic Search**: Uses vector embeddings for intelligent document retrieval
- 💬 **Interactive Chat**: Streamlit-based web interface for easy interaction
- 🧠 **RAG Architecture**: Combines retrieval and generation for accurate, context-aware answers
- 📚 **Source Citation**: Shows source documents for transparency

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
   - Use the sidebar to upload your archaeological survey PDF
   - Or click "Process Default PDF" if the PDF is in the parent directory
   - Click "Process PDF and Initialize System"
   - Wait for the system to process the document (this may take a few minutes)
   - **Note:** If you ran `setup.py`, the vector store is already created and you can click "Load Existing Vector Store"

4. **Start chatting:**
   - Once processed, you can ask questions about archaeological surveys
   - The chatbot will provide answers based on the PDF content
   - View source citations to see where the information came from

## Project Structure

```
archaeological-rag-chatbot/
├── app.py                 # Streamlit web application
├── pdf_processor.py       # PDF text extraction and chunking
├── vector_store.py        # Vector embeddings and FAISS/Chroma storage
├── rag_chain.py          # RAG chain implementation
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── README.md            # This file
└── vector_store/        # Generated vector store (created after processing)
```

## How It Works

1. **PDF Processing**: The PDF is processed to extract text, which is then split into manageable chunks
2. **Embedding Creation**: Text chunks are converted to vector embeddings using sentence transformers
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
- **Embedding Model**: Change `embedding_model` in `vector_store.py` (default: "sentence-transformers/all-MiniLM-L6-v2")
- **LLM Model**: Modify `model_name` in `rag_chain.py` (default: "gpt-3.5-turbo")
- **Temperature**: Adjust `temperature` for more/less creative responses (default: 0.7)

## Troubleshooting

### "OPENAI_API_KEY not found"
- Make sure you've created a `.env` file with your OpenAI API key
- Check that the `.env` file is in the same directory as `app.py`

### PDF Processing Errors
- Try a different PDF if the current one fails to process
- Some PDFs with complex layouts may require manual text extraction

### Vector Store Issues
- Delete the `vector_store/` directory and reprocess the PDF
- Make sure you have write permissions in the project directory

## Dependencies

- **streamlit**: Web interface
- **langchain**: RAG framework
- **langchain-openai**: OpenAI integration
- **pdfplumber/pypdf2**: PDF processing
- **faiss-cpu**: Vector similarity search
- **sentence-transformers**: Text embeddings
- **openai**: OpenAI API client

## License

This project is provided as-is for educational and research purposes.

## Contributing

Feel free to submit issues or pull requests to improve the chatbot!

