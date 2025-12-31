# Architecture Overview

## System Components

### 1. PDF Processor (`pdf_processor.py`)
- **Purpose**: Extracts text from PDF documents
- **Methods**:
  - `extract_text()`: Main extraction method (tries pdfplumber first, falls back to PyPDF2)
  - `chunk_text()`: Splits text into manageable chunks with overlap
- **Output**: List of text chunks ready for embedding

### 2. Vector Store Manager (`vector_store.py`)
- **Purpose**: Manages document embeddings and similarity search
- **Components**:
  - **Embeddings**: Uses HuggingFace sentence transformers (default: `all-MiniLM-L6-v2`)
  - **Vector Database**: FAISS or Chroma for fast similarity search
  - **Text Splitter**: RecursiveCharacterTextSplitter for intelligent chunking
- **Features**:
  - Create new vector stores from text chunks
  - Load existing vector stores from disk
  - Similarity search with configurable k (number of results)

### 3. RAG Chain (`rag_chain.py`)
- **Purpose**: Implements Retrieval-Augmented Generation
- **Components**:
  - **LLM**: OpenAI GPT-3.5-turbo (configurable)
  - **Retriever**: Vector store retriever with top-k search
  - **Prompt Template**: Custom prompt for archaeological survey context
  - **QA Chain**: LangChain RetrievalQA chain
- **Flow**:
  1. User asks a question
  2. Question is embedded and used to retrieve relevant document chunks
  3. Retrieved chunks + question are passed to LLM
  4. LLM generates answer based on retrieved context
  5. Answer + source documents are returned

### 4. Web Application (`app.py`)
- **Framework**: Streamlit
- **Features**:
  - PDF upload and processing interface
  - Chat interface with message history
  - Source citation display
  - Vector store management (load/create)

## Data Flow

```
PDF Document
    ↓
PDF Processor (extract & chunk)
    ↓
Text Chunks
    ↓
Vector Store Manager (embed & store)
    ↓
FAISS/Chroma Vector Database
    ↓
User Question
    ↓
RAG Chain (retrieve & generate)
    ↓
Answer + Sources
```

## Technology Stack

- **Web Framework**: Streamlit
- **RAG Framework**: LangChain
- **Embeddings**: Sentence Transformers (HuggingFace)
- **Vector Database**: FAISS (CPU) or Chroma
- **LLM**: OpenAI GPT-3.5-turbo
- **PDF Processing**: pdfplumber, PyPDF2

## Configuration Options

### Embedding Model
- Default: `sentence-transformers/all-MiniLM-L6-v2`
- Can be changed to other HuggingFace models
- Location: `vector_store.py`

### Chunk Size
- Default: 1000 characters
- Overlap: 200 characters
- Location: `pdf_processor.py` and `vector_store.py`

### LLM Model
- Default: `gpt-3.5-turbo`
- Temperature: 0.7
- Location: `rag_chain.py`

### Retrieval Parameters
- Default k (number of retrieved chunks): 4
- Location: `rag_chain.py`

## File Structure

```
archaeological-rag-chatbot/
├── app.py                 # Streamlit web app
├── pdf_processor.py       # PDF text extraction
├── vector_store.py        # Embeddings & vector DB
├── rag_chain.py          # RAG implementation
├── setup.py              # Setup script
├── requirements.txt      # Dependencies
├── README.md            # Main documentation
├── QUICKSTART.md        # Quick start guide
├── ARCHITECTURE.md      # This file
├── .env.example         # Environment template
└── vector_store/        # Generated (after setup)
    ├── index.faiss      # FAISS index
    └── index.pkl        # Metadata
```

## Performance Considerations

- **First Run**: PDF processing and embedding creation takes 5-10 minutes
- **Subsequent Runs**: Instant (vector store is cached)
- **Query Time**: 2-5 seconds (depends on API response time)
- **Memory**: ~500MB-1GB for typical PDFs

## Extensibility

The system can be extended to:
- Support multiple PDFs
- Use local LLMs (Ollama, etc.)
- Add different embedding models
- Implement conversation memory
- Add user authentication
- Export chat history

