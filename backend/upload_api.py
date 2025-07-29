"""
FastAPI Upload Service for PDF Files
Handles file uploads and automatically processes them with RAG pipeline
"""

import os
import io
import json
import uuid
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import PyPDF2

# Load environment variables from secrets
backend_root = Path(__file__).parent
secrets_path = backend_root / "secrets" / ".env"
load_dotenv(secrets_path)

# Configuration - RAG 구조에 맞게 통일
RAG_BASE_DIR = Path("rag")
UPLOAD_DIR = RAG_BASE_DIR / "data" / "pdf"  # RAG PDF 디렉토리와 통일
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# FastAPI app
app = FastAPI(
    title="Stockreport PDF Upload Service",
    description="Handles PDF uploads and automatically processes them with RAG pipeline",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class UploadResponse(BaseModel):
    fileId: str
    pages: Optional[int] = None
    filename: str
    uploadedAt: str
    processingStatus: str = "queued"  # queued, processing, completed, failed


class ChunkInfo(BaseModel):
    chunk_id: str
    page: int
    bbox_norm: List[float]  # [left, top, right, bottom] normalized 0-1
    label: Optional[str] = None


class FileMetadata(BaseModel):
    file_id: str
    original_filename: str
    saved_filename: str  # RAG에서 사용하는 실제 파일명
    page_count: int
    upload_timestamp: str


# Helper functions
def get_pdf_page_count(file_path: Path) -> int:
    """Extract page count from PDF file"""
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return len(pdf_reader.pages)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return 0


def save_file_metadata(metadata: FileMetadata) -> None:
    """Save simple file metadata"""
    metadata_file = UPLOAD_DIR / f"{metadata.file_id}_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata.dict(), f, ensure_ascii=False, indent=2)


def load_file_metadata(file_id: str) -> Optional[FileMetadata]:
    """Load file metadata"""
    metadata_file = UPLOAD_DIR / f"{file_id}_metadata.json"
    if not metadata_file.exists():
        return None
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return FileMetadata(**data)
    except Exception as e:
        print(f"Error loading file metadata: {e}")
        return None


def get_rag_results(saved_filename: str) -> Optional[Dict[str, Any]]:
    """RAG 결과 파일에서 직접 데이터 로드"""
    base_filename = saved_filename.replace('.pdf', '')
    rag_result_files = list(UPLOAD_DIR.glob(f"{base_filename}_*.json"))
    
    if not rag_result_files:
        return None
    
    try:
        rag_result_file = rag_result_files[0]
        with open(rag_result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading RAG results: {e}")
        return None


def get_rag_processing_status(saved_filename: str) -> str:
    """RAG 처리 상태 확인"""
    # 1. PDF 파일이 있는지 확인
    pdf_file = UPLOAD_DIR / saved_filename
    if not pdf_file.exists():
        return "not_found"
    
    # 2. RAG 결과 파일이 있는지 확인
    base_filename = saved_filename.replace('.pdf', '')
    rag_result_files = list(UPLOAD_DIR.glob(f"{base_filename}_*.json"))
    
    if rag_result_files:
        return "completed"
    else:
        return "pending"


async def process_pdf_with_rag(file_id: str, saved_filename: str):
    """
    Background task to process PDF with RAG pipeline
    """
    try:
        print(f"🚀 Starting RAG processing for {saved_filename}")
        
        # Change to RAG directory for execution
        original_cwd = os.getcwd()
        os.chdir(RAG_BASE_DIR)
        
        try:
            # Execute RAG processing with the specific file
            result = subprocess.run(
                ["python", "scripts/process_pdfs.py", "--limit", "1"],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                print(f"✅ RAG processing completed successfully for {saved_filename}")
                
                # Check if RAG result file was created
                base_filename = saved_filename.replace('.pdf', '')
                rag_result_files = list(UPLOAD_DIR.glob(f"{base_filename}_*.json"))
                
                if rag_result_files:
                    print(f"📄 RAG results available: {[f.name for f in rag_result_files]}")
                else:
                    print(f"⚠️ No RAG result files found for {saved_filename}")
                
            else:
                print(f"❌ RAG processing failed for {saved_filename}")
                print(f"Error output: {result.stderr}")
                    
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
            
    except subprocess.TimeoutExpired:
        print(f"⏰ RAG processing timeout for {saved_filename}")
    except Exception as e:
        print(f"💥 RAG processing error for {saved_filename}: {str(e)}")


# API Endpoints
@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a PDF file and automatically start RAG processing
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE/1024/1024}MB"
        )
    
    # Generate unique file ID and clean filename
    clean_filename = Path(file.filename).stem
    file_id = f"{uuid.uuid4().hex}_{clean_filename}"
    
    # Save to RAG PDF directory
    file_path = UPLOAD_DIR / f"{clean_filename}.pdf"  # Use original filename for RAG compatibility
    
    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(contents)
        print(f"📁 Saved PDF to: {file_path}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Get page count
    page_count = get_pdf_page_count(file_path)
    
    # Save simple metadata
    metadata = FileMetadata(
        file_id=file_id,
        original_filename=file.filename,
        saved_filename=clean_filename + ".pdf",
        page_count=page_count,
        upload_timestamp=datetime.now().isoformat()
    )
    save_file_metadata(metadata)
    
    # Add background task for RAG processing
    background_tasks.add_task(process_pdf_with_rag, file_id, clean_filename + ".pdf")
    
    print(f"🎯 Queued RAG processing for: {file.filename}")
    
    return UploadResponse(
        fileId=file_id,
        pages=page_count if page_count > 0 else None,
        filename=file.filename,
        uploadedAt=datetime.now().isoformat(),
        processingStatus="queued"
    )


@app.get("/status/{file_id}")
async def get_processing_status(file_id: str):
    """
    Get processing status for a file
    """
    metadata = load_file_metadata(file_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # RAG 처리 상태 및 결과 확인
    rag_status = get_rag_processing_status(metadata.saved_filename)
    rag_results = get_rag_results(metadata.saved_filename) if rag_status == "completed" else None
    
    return {
        "fileId": file_id,
        "filename": metadata.original_filename,
        "pages": metadata.page_count,
        "uploadedAt": metadata.upload_timestamp,
        "ragProcessingStatus": rag_status,
        "summaryStats": {
            "textSummaries": len(rag_results.get("text_summary", {}) if rag_results else {}),
            "imageSummaries": len(rag_results.get("image_summary", {}) if rag_results else {}),
            "tableSummaries": len(rag_results.get("table_summary", {}) if rag_results else {})
        }
    }


@app.get("/summaries/{file_id}")
async def get_summaries(file_id: str):
    """
    Get RAG processing results (text, image, table summaries)
    """
    metadata = load_file_metadata(file_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # RAG 결과 직접 로드
    rag_results = get_rag_results(metadata.saved_filename)
    if not rag_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RAG results not found - processing may not be completed yet"
        )
    
    return {
        "fileId": file_id,
        "filename": metadata.original_filename,
        "ragProcessingStatus": "completed",
        "summaries": {
            "textSummaries": rag_results.get("text_summary", {}),
            "imageSummaries": rag_results.get("image_summary", {}),
            "tableSummaries": rag_results.get("table_summary", {})
        },
        "stats": {
            "textCount": len(rag_results.get("text_summary", {})),
            "imageCount": len(rag_results.get("image_summary", {})),
            "tableCount": len(rag_results.get("table_summary", {}))
        }
    }


@app.get("/chunks/{file_id}", response_model=List[ChunkInfo])
async def get_chunks(file_id: str):
    """
    Get chunk information for a file  
    Returns empty array if no chunks are processed yet
    """
    metadata = load_file_metadata(file_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # RAG 결과에서 chunk 정보 로드 (현재는 빈 배열 반환)
    # TODO: RAG 결과에서 chunk/bbox 정보가 있다면 여기서 처리
    return []


@app.get("/file/{file_id}/download")
async def download_file(file_id: str):
    """Download the uploaded PDF file"""
    import urllib.parse
    
    print(f"Download request for file_id: {file_id}")
    
    # Extract filename from file_id (format: uuid_filename)
    if '_' in file_id:
        filename_part = '_'.join(file_id.split('_')[1:])
    else:
        filename_part = file_id
    
    # Try to find the file in RAG PDF directory
    file_path = None
    
    # Try exact filename match
    potential_path = UPLOAD_DIR / f"{filename_part}.pdf"
    if potential_path.exists():
        file_path = potential_path
    else:
        # Try to find any PDF file containing the filename
        for pdf_file in UPLOAD_DIR.glob("*.pdf"):
            if filename_part.lower() in pdf_file.stem.lower():
                file_path = pdf_file
                break
    
    if not file_path:
        print(f"File not found. Searched for: {filename_part}")
        print("Available files:")
        for file in UPLOAD_DIR.glob("*.pdf"):
            print(f"  - {file.name}")
            
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )
    
    # Read file and return as streaming response
    try:
        with open(file_path, 'rb') as f:
            pdf_content = f.read()
        
        # Use the actual filename for the response
        safe_filename = urllib.parse.quote(file_path.stem)
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{safe_filename}.pdf",
                "Content-Length": str(len(pdf_content)),
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check environment variables
    env_status = {
        "UPSTAGE_API_KEY": "✅" if os.getenv("UPSTAGE_API_KEY") else "❌",
        "OPENAI_API_KEY": "✅" if os.getenv("OPENAI_API_KEY") else "❌", 
        "CLOVASTUDIO_API_KEY": "✅" if os.getenv("CLOVASTUDIO_API_KEY") else "❌"
    }
    
    return {
        "status": "healthy",
        "service": "upload-api",
        "timestamp": datetime.now().isoformat(),
        "directories": {
            "upload_dir": str(UPLOAD_DIR)
        },
        "environment_variables": env_status
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Stockreport PDF Upload Service with RAG Integration",
        "version": "2.0.0",
        "endpoints": {
            "upload": "POST /upload - Upload PDF and start RAG processing",
            "status": "GET /status/{file_id} - Get processing status",
            "summaries": "GET /summaries/{file_id} - Get RAG results (text/image/table summaries)",
            "chunks": "GET /chunks/{file_id} - Get chunk information",
            "download": "GET /file/{file_id}/download - Download PDF",
            "health": "GET /health - Health check"
        },
        "features": [
            "Automatic RAG processing after upload",
            "Unified directory structure with RAG system",
            "Background task processing",
            "Processing status tracking"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    # Check environment on startup
    print("🔧 Checking environment variables...")
    required_vars = ["UPSTAGE_API_KEY", "OPENAI_API_KEY", "CLOVASTUDIO_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {missing_vars}")
        print(f"📁 Please ensure {secrets_path} contains the required API keys")
    else:
        print("✅ All required environment variables found")
    
    print(f"📁 Upload directory: {UPLOAD_DIR}")
    
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True) 