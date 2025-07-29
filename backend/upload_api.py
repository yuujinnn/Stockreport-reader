# -*- coding: utf-8 -*-
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
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import pymupdf  # fitz를 대신해서 pymupdf 사용

# uvicorn과 호환되는 로깅 설정
logger = logging.getLogger("uvicorn.error")  # uvicorn의 기본 로거 사용
logger.setLevel(logging.INFO)

# Load environment variables from secrets
backend_root = Path(__file__).parent
secrets_path = backend_root / "secrets" / ".env"
load_dotenv(secrets_path)

# Configuration - RAG 구조에 맞게 통일

# 현재 위치에서 rag 디렉토리 찾기 (backend에서 실행 vs 프로젝트 루트에서 실행)
current_dir = Path.cwd()
logger.info(f"🔧 Current working directory: {current_dir}")

if (current_dir / "rag").exists():
    # backend 디렉토리에서 실행
    RAG_BASE_DIR = Path("rag")
    logger.info(f"✅ Found rag directory in current path: {RAG_BASE_DIR.resolve()}")
elif (current_dir / "backend" / "rag").exists():
    # 프로젝트 루트에서 실행
    RAG_BASE_DIR = Path("backend") / "rag"
    logger.info(f"✅ Found rag directory in backend path: {RAG_BASE_DIR.resolve()}")
else:
    # 기본값
    RAG_BASE_DIR = Path("rag")
    logger.warning(f"⚠️ Using default rag path: {RAG_BASE_DIR.resolve()}")

UPLOAD_DIR = RAG_BASE_DIR / "data" / "pdf"  # RAG PDF 디렉토리와 통일
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

logger.info(f"📁 RAG_BASE_DIR: {RAG_BASE_DIR.resolve()}")
logger.info(f"📁 UPLOAD_DIR: {UPLOAD_DIR.resolve()}")
logger.info(f"📄 processed_states.json path: {(RAG_BASE_DIR / 'data' / 'vectordb' / 'processed_states.json').resolve()}")

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# FastAPI app
app = FastAPI(
    title="Stockreport PDF Upload Service",
    description="Handles PDF uploads and automatically processes them with RAG pipeline",
    version="2.0.0"
)

# 앱 로딩 확인용 간단한 테스트 엔드포인트
@app.get("/test")
async def test_endpoint():
    """앱이 제대로 로드되었는지 확인용 테스트 엔드포인트"""
    print("🧪 TEST ENDPOINT CALLED!")
    return {"status": "working", "message": "FastAPI app is loaded correctly"}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    print("🚀 Starting Stockreport PDF Upload Service")
    print("🌐 Available endpoints:")
    print("  • Test: http://localhost:9000/test")
    print("  • Root info: http://localhost:9000/")
    print("  • Upload PDF: POST http://localhost:9000/upload")
    print("  • Existing files: GET http://localhost:9000/files")
    print("  • Debug files: http://localhost:9000/debug/files")
    print("  • Debug uploads: http://localhost:9000/debug/uploads")
    print("  • Chunk data: http://localhost:9000/chunks/{file_id}")
    print("  • Health check: http://localhost:9000/health")
    print("🔍 Debugging steps:")
    print("  1. First check: http://localhost:9000/test")
    print("  2. Then check: http://localhost:9000/debug/files")
    print("  3. Get file_id: http://localhost:9000/debug/uploads")
    
    # 기존 PDF 파일들을 위한 메타데이터 자동 생성
    auto_generate_metadata_for_existing_pdfs()
    
    # 기존 파일 요약 출력
    summary = get_existing_files_summary()
    print(f"\n📊 File Summary:")
    print(f"  • PDF files: {len(summary['pdf_files'])}")
    print(f"  • Metadata files: {len(summary['metadata_files'])}")
    print(f"  • Processed files: {len(summary['processed_files'])}")
    
    if summary['processed_files']:
        print(f"  • Ready to use: {summary['processed_files']}")
    
    # FastAPI 앱의 등록된 엔드포인트들 확인
    print("\n📋 Registered FastAPI routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"  • {', '.join(route.methods)} {route.path}")
    
    # Environment variables check
    required_vars = ["UPSTAGE_API_KEY", "OPENAI_API_KEY", "CLOVASTUDIO_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {missing_vars}")
    else:
        print("✅ All required environment variables found")


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
    chunk_type: str  # "text", "image", "table"
    content: str  # 텍스트 내용 또는 요약
    label: Optional[str] = None
    # 페이지 크기 정보 추가 (RAG 파이프라인에서 사용한 실제 크기)
    page_width: Optional[float] = None
    page_height: Optional[float] = None
    # 원본 픽셀 좌표 추가 (디버깅 및 재계산용)
    bbox_pixels: Optional[List[int]] = None  # [left, top, right, bottom] in pixels


class FileMetadata(BaseModel):
    file_id: str
    original_filename: str
    saved_filename: str  # RAG에서 사용하는 실제 파일명
    page_count: int
    upload_timestamp: str


# Helper functions
def get_pdf_page_count(file_path: Path) -> int:
    """Extract page count from PDF file using pymupdf"""
    try:
        with pymupdf.open(file_path) as doc:
            return len(doc)
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
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
        logger.error(f"Error loading file metadata: {e}")
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


def get_processed_states() -> Optional[Dict[str, Any]]:
    """processed_states.json 파일에서 데이터 로드"""
    vectordb_dir = RAG_BASE_DIR / "data" / "vectordb"
    processed_states_file = vectordb_dir / "processed_states.json"
    
    logger.info(f"🔍 Looking for processed_states.json at: {processed_states_file}")
    logger.info(f"📁 Vectordb directory exists: {vectordb_dir.exists()}")
    logger.info(f"📄 Processed states file exists: {processed_states_file.exists()}")
    
    if not processed_states_file.exists():
        logger.warning("❌ processed_states.json file not found")
        return None
    
    try:
        with open(processed_states_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"✅ Loaded processed_states.json with {len(data)} files")
            logger.info(f"📋 Available files: {list(data.keys())}")
            return data
    except Exception as e:
        logger.error(f"❌ Error loading processed states: {e}")
        return None


def normalize_bbox(bbox_points: List[Dict[str, int]], page_width: float, page_height: float) -> List[float]:
    """바운딩박스 좌표를 정규화 (0-1 범위)"""
    try:
        # 4개 점에서 최소/최대값 추출
        x_coords = [point['x'] for point in bbox_points]
        y_coords = [point['y'] for point in bbox_points]
        
        left = min(x_coords) / page_width
        right = max(x_coords) / page_width
        top = min(y_coords) / page_height
        bottom = max(y_coords) / page_height
        
        return [left, top, right, bottom]
    except Exception as e:
        logger.error(f"Error normalizing bbox: {e}")
        return [0.0, 0.0, 1.0, 1.0]


def get_pdf_page_dimensions(file_path: Path, page_num: int = 0) -> tuple[float, float]:
    """PDF 페이지의 크기를 구함 (width, height) - pymupdf 사용"""
    try:
        with pymupdf.open(file_path) as doc:
            if page_num < len(doc):
                page = doc[page_num]
                # pymupdf에서 get_pixmap()을 사용해서 실제 렌더링된 크기를 구함
                # DPI 300으로 고정 (RAG 파이프라인과 동일)
                pixmap = page.get_pixmap(dpi=300)
                width = float(pixmap.width)
                height = float(pixmap.height)
                logger.info(f"📐 Page {page_num} dimensions (pymupdf): {width}x{height}")
                return width, height
    except Exception as e:
        logger.error(f"Error getting PDF page dimensions: {e}")
    
    # 기본값 반환 (A4 크기, 300 DPI)
    return 2480.0, 3508.0  # A4 at 300 DPI


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
        logger.info(f"🚀 Starting RAG processing for {saved_filename}")
        
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
                logger.info(f"✅ RAG processing completed successfully for {saved_filename}")
                
                # Check if RAG result file was created
                base_filename = saved_filename.replace('.pdf', '')
                rag_result_files = list(UPLOAD_DIR.glob(f"{base_filename}_*.json"))
                
                if rag_result_files:
                    logger.info(f"📄 RAG results available: {[f.name for f in rag_result_files]}")
                else:
                    logger.warning(f"⚠️ No RAG result files found for {saved_filename}")
                
            else:
                logger.error(f"❌ RAG processing failed for {saved_filename}")
                logger.error(f"Error output: {result.stderr}")
                    
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
            
    except subprocess.TimeoutExpired:
        logger.warning(f"⏰ RAG processing timeout for {saved_filename}")
    except Exception as e:
        logger.error(f"💥 RAG processing error for {saved_filename}: {str(e)}")


def auto_generate_metadata_for_existing_pdfs():
    """
    서버 시작 시 기존 PDF 파일들을 스캔해서 메타데이터가 없으면 자동 생성
    """
    logger.info("🔍 Scanning for existing PDF files without metadata...")
    
    if not UPLOAD_DIR.exists():
        logger.info("📁 Upload directory doesn't exist yet")
        return
    
    pdf_files = list(UPLOAD_DIR.glob("*.pdf"))
    logger.info(f"📄 Found {len(pdf_files)} PDF files")
    
    generated_count = 0
    
    for pdf_file in pdf_files:
        # 메타데이터 파일이 이미 있는지 확인
        existing_metadata = list(UPLOAD_DIR.glob(f"*_{pdf_file.stem}_metadata.json"))
        
        if existing_metadata:
            logger.info(f"✅ Metadata already exists for {pdf_file.name}")
            continue
        
        # 메타데이터 생성
        try:
            page_count = get_pdf_page_count(pdf_file)
            file_id = f"{uuid.uuid4().hex}_{pdf_file.stem}"
            
            metadata = FileMetadata(
                file_id=file_id,
                original_filename=pdf_file.name,
                saved_filename=pdf_file.name,
                page_count=page_count,
                upload_timestamp=datetime.now().isoformat()
            )
            
            save_file_metadata(metadata)
            generated_count += 1
            
            logger.info(f"📋 Generated metadata for {pdf_file.name} with file_id: {file_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate metadata for {pdf_file.name}: {e}")
    
    if generated_count > 0:
        logger.info(f"🎉 Generated metadata for {generated_count} existing PDF files")
    else:
        logger.info("✨ All existing PDF files already have metadata")


def get_existing_files_summary():
    """
    기존 파일들의 요약 정보 반환
    """
    summary = {
        "pdf_files": [],
        "processed_files": [],
        "metadata_files": []
    }
    
    if UPLOAD_DIR.exists():
        # PDF 파일들
        pdf_files = list(UPLOAD_DIR.glob("*.pdf"))
        summary["pdf_files"] = [f.name for f in pdf_files]
        
        # 메타데이터 파일들
        metadata_files = list(UPLOAD_DIR.glob("*_metadata.json"))
        summary["metadata_files"] = [f.name for f in metadata_files]
    
    # processed_states.json에서 처리된 파일들
    processed_states = get_processed_states()
    if processed_states:
        summary["processed_files"] = list(processed_states.keys())
    
    return summary

# API Endpoints
@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a PDF file and automatically start RAG processing
    """
    # 임시 디버깅: print와 logger 둘 다 사용
    print(f"🎯 UPLOAD REQUEST RECEIVED: {file.filename}")
    logger.info(f"🎯 UPLOAD REQUEST RECEIVED: {file.filename}")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        print(f"❌ Invalid file type: {file.filename}")
        logger.error(f"❌ Invalid file type: {file.filename}")
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
        logger.info(f"📁 Saved PDF to: {file_path}")
    except Exception as e:
        print(f"❌ Failed to save file: {str(e)}")
        logger.error(f"Failed to save file: {str(e)}")
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
    print(f"📋 File metadata saved: {file_id}_metadata.json")
    print(f"📄 PDF saved as: {clean_filename}.pdf")
    print(f"🕐 Upload completed at: {datetime.now().isoformat()}")
    
    logger.info(f"🎯 Queued RAG processing for: {file.filename}")
    logger.info(f"📋 File metadata saved: {file_id}_metadata.json")
    logger.info(f"📄 PDF saved as: {clean_filename}.pdf")
    logger.info(f"🕐 Upload completed at: {datetime.now().isoformat()}")
    
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
    Get chunk information for a file from processed_states.json
    """
    logger.info(f"🔍 GET /chunks/{file_id} - Starting chunk retrieval")
    
    metadata = load_file_metadata(file_id)
    if not metadata:
        logger.error(f"❌ No metadata found for file_id: {file_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    logger.info(f"✅ Found metadata for file: {metadata.saved_filename}")
    
    # processed_states.json에서 데이터 로드
    processed_states = get_processed_states()
    if not processed_states:
        logger.warning("❌ No processed_states data available")
        return []
    
    # 파일명으로 데이터 찾기
    saved_filename = metadata.saved_filename
    logger.info(f"🔍 Looking for file data: {saved_filename}")
    
    if saved_filename not in processed_states:
        logger.warning(f"❌ File {saved_filename} not found in processed_states")
        logger.info(f"📋 Available files in processed_states: {list(processed_states.keys())}")
        return []
    
    logger.info(f"✅ Found processed data for: {saved_filename}")
    
    file_data = processed_states[saved_filename]
    chunks = []
    
    # PDF 파일 경로 구성
    pdf_file_path = UPLOAD_DIR / saved_filename
    
    try:
        # 각 청크 타입별로 처리
        chunk_types = [
            ("text_element_output", "text"),
            ("image_summary", "image"), 
            ("table_summary", "table")
        ]
        
        logger.info(f"📊 Processing chunk types for {saved_filename}")
        logger.info(f"📋 Available sections in file_data: {list(file_data.keys())}")
        
        for section_name, chunk_type in chunk_types:
            if section_name not in file_data:
                logger.warning(f"⚠️ Section {section_name} not found in file data")
                continue
                
            section_data = file_data[section_name]
            logger.info(f"✅ Processing {section_name} with {len(section_data)} chunks")
            
            for chunk_id, chunk_info in section_data.items():
                try:
                    # 데이터 파싱: [페이지번호, [바운딩박스좌표], "내용"]
                    page_num = chunk_info[0]
                    bbox_points = chunk_info[1]
                    content = chunk_info[2]
                    
                    # PDF 페이지 크기 구하기 (페이지별로 다를 수 있음)
                    page_width, page_height = get_pdf_page_dimensions(pdf_file_path, page_num)
                    
                    # 바운딩박스 정규화
                    bbox_norm = normalize_bbox(bbox_points, page_width, page_height)
                    
                    # 원본 픽셀 좌표 계산
                    x_coords = [point['x'] for point in bbox_points]
                    y_coords = [point['y'] for point in bbox_points]
                    bbox_pixels = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                    
                    # 라벨 생성 (청크 타입에 따라)
                    if chunk_type == "text":
                        # 텍스트의 첫 20자 또는 첫 줄을 라벨로 사용
                        first_line = content.split('\n')[0]
                        label = first_line[:20] + "..." if len(first_line) > 20 else first_line
                    elif chunk_type == "image":
                        label = f"이미지 #{chunk_id}"
                    else:  # table
                        label = f"테이블 #{chunk_id}"
                    
                    chunk = ChunkInfo(
                        chunk_id=f"{chunk_type}_{chunk_id}",
                        page=page_num + 1,  # 0-based를 1-based로 변환
                        bbox_norm=bbox_norm,
                        chunk_type=chunk_type,
                        content=content,
                        label=label,
                        page_width=page_width,
                        page_height=page_height,
                        bbox_pixels=bbox_pixels
                    )
                    chunks.append(chunk)
                    
                except (IndexError, KeyError, TypeError) as e:
                    logger.error(f"Error processing chunk {chunk_id} in {section_name}: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Error processing chunks for {saved_filename}: {e}")
        return []
    
    # 페이지 순서대로 정렬
    chunks.sort(key=lambda x: (x.page, x.chunk_id))
    
    logger.info(f"📦 Loaded {len(chunks)} chunks for {saved_filename}")
    return chunks


@app.get("/file/{file_id}/download")
async def download_file(file_id: str):
    """Download the uploaded PDF file"""
    import urllib.parse
    
    logger.info(f"Download request for file_id: {file_id}")
    
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
        logger.warning(f"File not found. Searched for: {filename_part}")
        available_files = [file.name for file in UPLOAD_DIR.glob("*.pdf")]
        logger.info(f"Available files: {available_files}")
            
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
        logger.error(f"Error reading file {file_path}: {e}")
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
    print("🏠 ROOT ENDPOINT CALLED!")
    return {
        "status": "running",
        "service": "Stockreport PDF Upload Service with RAG Integration",
        "version": "2.0.0",
        "message": "API is working correctly",
        "test_endpoint": "GET /test",
        "endpoints": {
            "upload": "POST /upload - Upload PDF and start RAG processing",
            "status": "GET /status/{file_id} - Get processing status",
            "summaries": "GET /summaries/{file_id} - Get RAG results (text/image/table summaries)",
            "chunks": "GET /chunks/{file_id} - Get chunk information",
            "download": "GET /file/{file_id}/download - Download PDF",
            "health": "GET /health - Health check",
            "debug_files": "GET /debug/files - Debug file system status",
            "debug_uploads": "GET /debug/uploads - Debug uploads status"
        },
        "features": [
            "Automatic RAG processing after upload",
            "Unified directory structure with RAG system", 
            "Background task processing",
            "Processing status tracking",
            "Chunk-based document analysis with bounding boxes"
        ]
    }


@app.get("/debug/files")
async def debug_files():
    """디버깅용 파일 상태 확인 엔드포인트"""
    vectordb_dir = RAG_BASE_DIR / "data" / "vectordb"
    processed_states_file = vectordb_dir / "processed_states.json"
    
    debug_info = {
        "current_working_directory": os.getcwd(),
        "rag_base_dir": str(RAG_BASE_DIR),
        "rag_base_dir_resolved": str(RAG_BASE_DIR.resolve()),
        "upload_dir": str(UPLOAD_DIR),
        "upload_dir_resolved": str(UPLOAD_DIR.resolve()),
        "vectordb_dir": str(vectordb_dir),
        "vectordb_dir_resolved": str(vectordb_dir.resolve()),
        "processed_states_file": str(processed_states_file),
        "processed_states_file_resolved": str(processed_states_file.resolve()),
        "directories": {
            "rag_base_exists": RAG_BASE_DIR.exists(),
            "upload_dir_exists": UPLOAD_DIR.exists(),
            "vectordb_dir_exists": vectordb_dir.exists(),
        },
        "files": {
            "processed_states_exists": processed_states_file.exists(),
        },
        "upload_dir_contents": [],
        "vectordb_contents": []
    }
    
    # Upload 디렉토리 내용
    if UPLOAD_DIR.exists():
        debug_info["upload_dir_contents"] = [f.name for f in UPLOAD_DIR.iterdir()]
    
    # Vectordb 디렉토리 내용  
    if vectordb_dir.exists():
        debug_info["vectordb_contents"] = [f.name for f in vectordb_dir.iterdir()]
    
    # processed_states.json 내용 미리보기
    if processed_states_file.exists():
        try:
            with open(processed_states_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                debug_info["processed_states_preview"] = {
                    "file_count": len(data),
                    "files": list(data.keys())
                }
        except Exception as e:
            debug_info["processed_states_error"] = str(e)
    
    return debug_info


@app.get("/debug/uploads")
async def debug_uploads():
    """업로드된 파일들과 file_id 목록 조회"""
    uploads_info = {
        "uploaded_files": [],
        "metadata_files": [],
        "instructions": {
            "how_to_get_file_id": "파일 업로드 후 응답의 'fileId' 필드를 사용하거나, 아래 metadata_files에서 확인",
            "chunk_api_format": "GET /chunks/{file_id}",
            "example": "GET /chunks/abc123_filename"
        }
    }
    
    if UPLOAD_DIR.exists():
        for file_path in UPLOAD_DIR.iterdir():
            if file_path.is_file():
                if file_path.name.endswith('_metadata.json'):
                    # 메타데이터 파일 파싱
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            uploads_info["metadata_files"].append({
                                "file_id": metadata.get("file_id"),
                                "original_filename": metadata.get("original_filename"),
                                "saved_filename": metadata.get("saved_filename"),
                                "upload_timestamp": metadata.get("upload_timestamp"),
                                "chunk_api_url": f"/chunks/{metadata.get('file_id')}"
                            })
                    except Exception as e:
                        uploads_info["metadata_files"].append({
                            "filename": file_path.name,
                            "error": str(e)
                        })
                else:
                    uploads_info["uploaded_files"].append(file_path.name)
    
    return uploads_info


@app.get("/files")
async def get_existing_files():
    """
    기존에 업로드된 파일들 목록 조회
    RAG 처리 상태와 함께 반환
    """
    files_info = []
    
    if not UPLOAD_DIR.exists():
        return {"files": files_info, "total": 0}
    
    # 메타데이터 파일들을 기준으로 파일 목록 구성
    metadata_files = list(UPLOAD_DIR.glob("*_metadata.json"))
    processed_states = get_processed_states()
    
    for metadata_file in metadata_files:
        try:
            metadata = load_file_metadata(metadata_file.stem.replace("_metadata", ""))
            if not metadata:
                continue
            
            # RAG 처리 상태 확인
            rag_status = "not_processed"
            has_chunks = False
            
            if processed_states and metadata.saved_filename in processed_states:
                file_data = processed_states[metadata.saved_filename]
                # 텍스트, 이미지, 테이블 중 하나라도 있으면 처리된 것으로 간주
                if (file_data.get("text_element_output") or 
                    file_data.get("image_summary") or 
                    file_data.get("table_summary")):
                    rag_status = "completed"
                    has_chunks = True
                elif file_data.get("parsing_processed"):
                    rag_status = "processing"
            
            file_info = {
                "file_id": metadata.file_id,
                "filename": metadata.original_filename,
                "saved_filename": metadata.saved_filename,
                "pages": metadata.page_count,
                "upload_timestamp": metadata.upload_timestamp,
                "rag_status": rag_status,
                "has_chunks": has_chunks,
                "download_url": f"/file/{metadata.file_id}/download",
                "chunks_url": f"/chunks/{metadata.file_id}" if has_chunks else None
            }
            
            files_info.append(file_info)
            
        except Exception as e:
            logger.error(f"Error processing metadata file {metadata_file}: {e}")
            continue
    
    # 업로드 시간순으로 정렬 (최신순)
    files_info.sort(key=lambda x: x["upload_timestamp"], reverse=True)
    
    return {
        "files": files_info,
        "total": len(files_info),
        "summary": {
            "total_files": len(files_info),
            "rag_completed": len([f for f in files_info if f["rag_status"] == "completed"]),
            "rag_processing": len([f for f in files_info if f["rag_status"] == "processing"]),
            "not_processed": len([f for f in files_info if f["rag_status"] == "not_processed"])
        }
    }


# Note: When using uvicorn command directly, this block is not executed
# All startup logging is handled in the @app.on_event("startup") function above
if __name__ == "__main__":
    import uvicorn
    
    # This will only run when executing: python upload_api.py
    # For uvicorn command: uvicorn upload_api:app --host 0.0.0.0 --port 9000 --reload
    logger.info("🔧 Starting server via python upload_api.py")
    logger.info("📄 Note: For production use 'uvicorn upload_api:app --host 0.0.0.0 --port 9000 --reload'")
    
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=True) 