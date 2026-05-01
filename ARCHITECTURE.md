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
  - **Embeddings**: Uses OpenAI embeddings (default: `text-embedding-3-small`)
  - **Vector Database**: FAISS for fast similarity search
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
  - Script-aware artifact image analysis with enhancement, OCR metadata, and manual review hotspots
  - Lightweight external similar-finds lookup

### 5. Artifact Lookup (`artifact_lookup.py`)
- **Purpose**: Suggest comparable public collection records without bundling local reference corpora
- **Sources**:
  - The Met public collection API
  - Wikidata search API
  - Europeana search API when `EUROPEANA_API_KEY` is configured

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
FAISS Vector Database
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
- **Embeddings**: OpenAI Embeddings
- **Vector Database**: FAISS (CPU)
- **LLM**: OpenAI GPT-3.5-turbo
- **PDF Processing**: pdfplumber, PyPDF2
- **Artifact Similarity**: public collection APIs

## Configuration Options

### Embedding Model
- Default: `text-embedding-3-small`
- Can be changed to other OpenAI embedding models
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
├── artifact_lookup.py   # Public collection lookup adapters
└── vector_store/        # Generated locally or at runtime, not committed
```

## Performance Considerations

- **First Run**: PDF processing and embedding creation takes 5-10 minutes
- **Subsequent Runs**: Instant (vector store is cached)
- **Query Time**: 2-5 seconds (depends on API response time)
- **Memory**: ~500MB-1GB for typical PDFs

For Streamlit Community Cloud:
- Keep runtime data out of git
- Use temporary in-browser session state by default (open access, no login)
- Build or fetch vector indexes outside the repository

## Extensibility

The system can be extended to:
- Support multiple PDFs
- Use local LLMs (Ollama, etc.)
- Add different embedding models
- Implement conversation memory
- Export chat history

