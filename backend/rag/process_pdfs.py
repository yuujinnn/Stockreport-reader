import re
import sys
import time
import os
import logging
import argparse
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from pathlib import Path
from dotenv import load_dotenv
from src.vectorstore import VectorStore
from src.parser import process_single_pdf
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from langchain.schema import Document

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parents[3]  # Stockreport-reader/
load_dotenv(project_root / "backend/secrets/.env")


def load_processed_states():
    """Load the list of processed PDF files."""
    processed_states_path = Path("./data/vectordb/processed_states.json")
    if processed_states_path.exists():
        with open(processed_states_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def is_original_pdf(filename: str, processed_states: dict) -> bool:
    """Check if file is an original PDF that hasn't been processed yet."""
    if filename in processed_states:
        return False

    # Skip split PDF files (pattern: _YYYY_ZZZZ.pdf)
    split_pattern = r"_\d{4}_\d{4}\.pdf$"
    return filename.endswith(".pdf") and not re.search(split_pattern, filename)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((Exception, ValueError)),
)
def process_single_pdf_with_retry(pdf_path, processing_uid):
    """Process a single PDF with retry logic."""
    try:
        state = process_single_pdf(pdf_path, processing_uid)
        if state is None:
            raise ValueError(f"PDF processing failed: {pdf_path}")
        return state
    except Exception as e:
        logger.error(f"Error during PDF processing retry: {str(e)}")
        raise


def validate_and_process_pdf(pdf_path):
    """Validate and process a single PDF file."""
    try:
        logger.info(f"=== Starting PDF processing: {pdf_path} ===")

        # PDF file validation
        if not os.path.exists(pdf_path):
            raise ValueError(f"PDF file does not exist: {pdf_path}")

        if os.path.getsize(pdf_path) == 0:
            raise ValueError(f"PDF file is empty: {pdf_path}")

        # Process PDF using the parser
        try:
            from src.parser import process_single_pdf as parser_process_pdf

            state = parser_process_pdf(pdf_path)

            # Validate processing results
            if state is None:
                raise ValueError(f"No processing results: {pdf_path}")

            required_keys = [
                "text_summary",
                "text_element_output", 
                "image_summary",
                "table_summary",
            ]
            missing_keys = [key for key in required_keys if key not in state]
            if missing_keys:
                logger.warning(f"Missing keys: {missing_keys}")
                # Add empty dictionaries for missing keys
                for key in missing_keys:
                    state[key] = {}

            logger.info(f"PDF processing completed: {os.path.basename(pdf_path)}")
            logger.info(f"Processed data keys: {list(state.keys())}")
            return state

        except Exception as e:
            logger.error(f"Error during PDF parsing: {str(e)}", exc_info=True)
            # Return default state
            return {
                "text_summary": {},
                "text_element_output": {},
                "image_summary": {},
                "table_summary": {},
            }

    except Exception as e:
        logger.error(f"Critical error during PDF processing: {str(e)}", exc_info=True)
        return None


def process_new_pdfs(limit: int = None):
    """Process new PDF files and save states locally.

    Args:
        limit (int, optional): Maximum number of PDF files to process. 
                              Defaults to None (process all files).
    """
    pdf_directory = "./data/pdf"
    processed_states_path = Path("./data/vectordb/processed_states.json")
    processed_states = load_processed_states()

    # Debug: print existing state
    logger.info(f"\n=== Current Processing State ===")
    logger.info(f"Number of processed files: {len(processed_states)}")

    # Filter new original PDF files only
    pdf_files = [
        f for f in os.listdir(pdf_directory) if is_original_pdf(f, processed_states)
    ]

    # Limit number of files if specified
    if limit is not None:
        pdf_files = pdf_files[:limit]
        logger.info(f"Limiting processing to {limit} files.")

    logger.info(f"\n=== New PDF Files Info ===")
    logger.info(f"New PDF files to process: {len(pdf_files)}")
    logger.info(f"PDF file list: {pdf_files}")

    if not pdf_files:
        logger.info("No new PDF files to process.")
        return

    # Initialize VectorStore for ChromaDB storage
    vector_store = VectorStore(persist_directory="./data/vectordb")

    for pdf_file in pdf_files:
        try:
            pdf_path = os.path.join(pdf_directory, pdf_file)
            processing_uid = str(uuid.uuid4().hex)  # Use hex format to match upload_api.py
            
            # 순차 처리로 Rate Limit 준수
            logger.info(f"Processing {pdf_file} sequentially to avoid rate limits...")
            state = process_single_pdf_with_retry(pdf_path, processing_uid)

            if state is None:
                logger.error(f"PDF processing failed: {pdf_file}")
                continue

            # Debug: print state before merging
            logger.info(f"\n=== Pre-merge State ({pdf_file}) ===")
            if pdf_file in processed_states:
                logger.info(f"Existing state: {processed_states[pdf_file]}")
            else:
                logger.info("No existing state")

            # Update state information
            state_dict = {
                "text_summary": state.get("text_summary", {}),
                "text_element_output": state.get("text_element_output", {}),
                "image_summary": state.get("image_summary", {}),
                "table_summary": state.get("table_summary", {}),
                "parsing_processed": True,
                "vectorstore_processed": True,
                "processing_uid": processing_uid,
            }

            # Debug: print new state
            logger.info(f"New state: {state_dict}")

            # Merge with existing state information
            if pdf_file in processed_states:
                processed_states[pdf_file].update(state_dict)
                logger.info(f"State merge completed: {processed_states[pdf_file]}")
            else:
                processed_states[pdf_file] = state_dict
                logger.info("New state added")

            logger.info(f"\n=== Processing Completed: {pdf_file} ===")
            logger.info(f"Text summaries: {len(state_dict['text_summary'])}")
            logger.info(f"Text elements: {len(state_dict['text_element_output'])}")
            logger.info(f"Image summaries: {len(state_dict['image_summary'])}")
            logger.info(f"Table summaries: {len(state_dict['table_summary'])}")

            # Store page-level text summaries in ChromaDB
            if state.get("text_summary"):
                documents = [
                    Document(
                        page_content=text,
                        metadata={"source": pdf_file, "type": "text_summary"},
                    )
                    for text in state.get("text_summary", {}).values()
                    if text.strip()  # Only add non-empty content
                ]
                
                if documents:
                    vector_store.add_documents(documents)
                    logger.info(f"Added {len(documents)} documents to ChromaDB")

            # Save state file
            with open(processed_states_path, "w", encoding="utf-8") as f:
                json.dump(processed_states, f, ensure_ascii=False, indent=2)
            logger.info("State file saved successfully")

        except Exception as e:
            logger.error(f"Processing failed ({pdf_file}): {str(e)}")
            continue

    logger.info(f"\n=== Processing Summary ===")
    logger.info(f"Total processed files: {len([f for f in processed_states if processed_states[f].get('parsing_processed')])}")
    logger.info(f"Files in vector database: {len([f for f in processed_states if processed_states[f].get('vectorstore_processed')])}")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="PDF processing script for RAG pipeline")
    parser.add_argument("--limit", type=int, help="Maximum number of PDF files to process")
    parser.add_argument("--processing-uid", type=str, help="Specific processing UID to use")
    parser.add_argument("--filename", type=str, help="Specific filename to process")
    args = parser.parse_args()

    # Validate required environment variables
    required_env_vars = ["UPSTAGE_API_KEY", "OPENAI_API_KEY", "CLOVASTUDIO_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please ensure backend/secrets/.env contains the required API keys")
        sys.exit(1)

    # Ensure required directories exist
    os.makedirs("./data/pdf", exist_ok=True)
    os.makedirs("./data/vectordb", exist_ok=True)
    os.makedirs("./data/logs", exist_ok=True)

    if args.filename and args.processing_uid:
        # Process specific file with specific UID
        process_specific_pdf(args.filename, args.processing_uid)
    else:
        # Process new PDFs with auto-generated UIDs
        process_new_pdfs(limit=args.limit)


def process_specific_pdf(filename: str, processing_uid: str):
    """Process a specific PDF file with a given processing UID."""
    pdf_directory = "./data/pdf"
    processed_states_path = Path("./data/vectordb/processed_states.json")
    processed_states = load_processed_states()
    
    pdf_path = os.path.join(pdf_directory, filename)
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    logger.info(f"🎯 Processing specific file: {filename} with UID: {processing_uid}")
    
    # Initialize VectorStore for ChromaDB storage
    vector_store = VectorStore(persist_directory="./data/vectordb")
    
    try:
        state = process_single_pdf_with_retry(pdf_path, processing_uid)
        
        if state is None:
            logger.error(f"PDF processing failed: {filename}")
            return
        
        # Update state information
        state_dict = {
            "text_summary": state.get("text_summary", {}),
            "text_element_output": state.get("text_element_output", {}),
            "image_summary": state.get("image_summary", {}),
            "table_summary": state.get("table_summary", {}),
            "parsing_processed": True,
            "vectorstore_processed": True,
            "processing_uid": processing_uid,
        }
        
        # Merge with existing state information
        if filename in processed_states:
            processed_states[filename].update(state_dict)
            logger.info(f"State merge completed for: {filename}")
        else:
            processed_states[filename] = state_dict
            logger.info(f"New state added for: {filename}")
        
        logger.info(f"✅ Processing Completed: {filename}")
        logger.info(f"Text summaries: {len(state_dict['text_summary'])}")
        logger.info(f"Text elements: {len(state_dict['text_element_output'])}")
        logger.info(f"Image summaries: {len(state_dict['image_summary'])}")
        logger.info(f"Table summaries: {len(state_dict['table_summary'])}")
        
        # Store page-level text summaries in ChromaDB
        if state.get("text_summary"):
            documents = [
                Document(
                    page_content=text,
                    metadata={"source": filename, "type": "text_summary"},
                )
                for text in state.get("text_summary", {}).values()
                if text.strip()  # Only add non-empty content
            ]
            
            if documents:
                vector_store.add_documents(documents)
                logger.info(f"Added {len(documents)} documents to ChromaDB")
        
        # Save state file
        with open(processed_states_path, "w", encoding="utf-8") as f:
            json.dump(processed_states, f, ensure_ascii=False, indent=2)
        logger.info("State file saved successfully")
        
    except Exception as e:
        logger.error(f"Processing failed ({filename}): {str(e)}")


if __name__ == "__main__":
    main()
