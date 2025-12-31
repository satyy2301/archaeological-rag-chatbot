"""
Setup script to initialize the RAG chatbot system
Processes the PDF and creates the vector store
"""

import os
import sys
from pathlib import Path
from pdf_processor import PDFProcessor
from vector_store import VectorStoreManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_pdf_file():
    """Find the archaeological PDF file"""
    possible_paths = [
        "../archelogical pdf pr0ooject.pdf",
        "archelogical pdf pr0ooject.pdf",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "archelogical pdf pr0ooject.pdf")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found PDF at: {path}")
            return path
    
    return None


def setup_vector_store(pdf_path: str):
    """Process PDF and create vector store"""
    logger.info("Starting PDF processing and vector store creation...")
    
    # Process PDF
    logger.info("Step 1: Processing PDF...")
    processor = PDFProcessor(pdf_path)
    text_chunks = processor.process(chunk_size=1000, chunk_overlap=200)
    
    if not text_chunks:
        logger.error("No text could be extracted from the PDF.")
        return False
    
    logger.info(f"✓ Extracted {len(text_chunks)} text chunks from PDF")
    
    # Create vector store
    logger.info("Step 2: Creating vector embeddings...")
    vector_store_manager = VectorStoreManager(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        vector_store_type="faiss",
        persist_directory="./vector_store"
    )
    vector_store_manager.create_vector_store(text_chunks)
    logger.info("✓ Vector store created successfully!")
    
    return True


def main():
    """Main setup function"""
    print("=" * 60)
    print("Archaeological Survey RAG Chatbot - Setup")
    print("=" * 60)
    print()
    
    # Check for PDF
    pdf_path = find_pdf_file()
    if not pdf_path:
        print("❌ Error: Could not find the archaeological PDF file.")
        print("Please make sure 'archelogical pdf pr0ooject.pdf' is in the parent directory")
        print("or provide the path manually.")
        sys.exit(1)
    
    # Check if vector store already exists
    if os.path.exists("./vector_store"):
        response = input("Vector store already exists. Recreate? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            sys.exit(0)
        import shutil
        shutil.rmtree("./vector_store")
        print("Removed existing vector store.")
    
    # Setup
    success = setup_vector_store(pdf_path)
    
    if success:
        print()
        print("=" * 60)
        print("✓ Setup completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Make sure you have set OPENAI_API_KEY in your .env file")
        print("2. Run: streamlit run app.py")
        print("3. Open the app in your browser")
    else:
        print()
        print("❌ Setup failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

