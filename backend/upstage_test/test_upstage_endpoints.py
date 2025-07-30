#!/usr/bin/env python3
"""
Upstage API 엔드포인트 테스트 스크립트
두 엔드포인트의 성능과 응답 형식을 비교합니다:
1. https://api.upstage.ai/v1/document-ai/layout-analysis 
2. https://api.upstage.ai/v1/document-digitization
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드 (프로젝트의 secrets/.env 파일에서)
project_root = Path(__file__).parent.parent
secrets_env_path = project_root / "secrets" / ".env"

if secrets_env_path.exists():
    load_dotenv(secrets_env_path)
    print(f"✅ Environment variables loaded from {secrets_env_path}")
else:
    print(f"⚠️  No .env file found at {secrets_env_path}")

# 환경 변수에서 API 키 로드
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    print("❌ UPSTAGE_API_KEY not found in environment variables.")
    print("🔧 Please set UPSTAGE_API_KEY in backend/secrets/.env file")
    print("   Format: UPSTAGE_API_KEY=your_api_key_here")
    
    # 대화형으로 API 키 입력 받기
    try:
        UPSTAGE_API_KEY = input("Enter your UPSTAGE_API_KEY: ").strip()
        if not UPSTAGE_API_KEY:
            raise ValueError("API key cannot be empty")
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Test cancelled by user")
        exit(1)
        
print(f"🔑 Using API key: {UPSTAGE_API_KEY[:8]}...{UPSTAGE_API_KEY[-4:]}")

# 테스트할 PDF 파일 경로
current_dir = Path(__file__).parent
PDF_FILE_PATH = current_dir / "20250730_SOOP (067160_매도) (2p).pdf"

# 결과 저장 디렉토리
RESULTS_DIR = current_dir / "results"
RESULTS_DIR.mkdir(exist_ok=True)

def test_layout_analysis_endpoint(file_path: str) -> dict:
    """
    document-ai/layout-analysis 엔드포인트 테스트
    """
    print("🔍 Testing Layout Analysis endpoint...")
    
    url = "https://api.upstage.ai/v1/document-ai/layout-analysis"
    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}"
    }
    
    start_time = time.time()
    
    try:
        with open(file_path, "rb") as file:
            files = {"document": file}
            response = requests.post(url, headers=headers, files=files)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        result = {
            "endpoint": "layout-analysis",
            "status_code": response.status_code,
            "processing_time_seconds": round(processing_time, 2),
            "timestamp": datetime.now().isoformat(),
            "success": response.status_code == 200
        }
        
        if response.status_code == 200:
            response_data = response.json()
            result["response_data"] = response_data
            result["response_type"] = type(response_data).__name__
            result["response_keys"] = list(response_data.keys()) if isinstance(response_data, dict) else None
            
            # 응답 데이터 크기 정보
            response_text = json.dumps(response_data, ensure_ascii=False)
            result["response_size_chars"] = len(response_text)
            result["response_size_kb"] = round(len(response_text.encode('utf-8')) / 1024, 2)
            
            print(f"✅ Layout Analysis - Success! (Processing time: {processing_time:.2f}s)")
            print(f"   Response size: {result['response_size_kb']} KB")
            
        else:
            result["error"] = {
                "status_code": response.status_code,
                "error_message": response.text
            }
            print(f"❌ Layout Analysis - Failed! Status: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        result = {
            "endpoint": "layout-analysis",
            "status_code": None,
            "processing_time_seconds": None,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": {
                "exception": str(e),
                "type": type(e).__name__
            }
        }
        print(f"❌ Layout Analysis - Exception: {str(e)}")
    
    return result

def test_document_digitization_endpoint(file_path: str) -> dict:
    """
    document-digitization 엔드포인트 테스트
    """
    print("🔍 Testing Document Digitization endpoint...")
    
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {
        "Authorization": f"Bearer {UPSTAGE_API_KEY}"
    }
    
    start_time = time.time()
    
    try:
        with open(file_path, "rb") as file:
            files = {"document": file}
            # Document Parse API - 최신 파라미터 형식
            data = {
                "model": "document-parse",
                "ocr": "force",
                "chart_recognition": True,
                "coordinates": True,
                "output_formats": '["html", "markdown"]',
                "base64_encoding": '["figure"]',
            }
            response = requests.post(url, headers=headers, files=files, data=data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        result = {
            "endpoint": "document-digitization",
            "status_code": response.status_code,
            "processing_time_seconds": round(processing_time, 2),
            "timestamp": datetime.now().isoformat(),
            "success": response.status_code == 200
        }
        
        if response.status_code == 200:
            response_data = response.json()
            result["response_data"] = response_data
            result["response_type"] = type(response_data).__name__
            result["response_keys"] = list(response_data.keys()) if isinstance(response_data, dict) else None
            
            # 응답 데이터 크기 정보
            response_text = json.dumps(response_data, ensure_ascii=False)
            result["response_size_chars"] = len(response_text)
            result["response_size_kb"] = round(len(response_text.encode('utf-8')) / 1024, 2)
            
            print(f"✅ Document Digitization - Success! (Processing time: {processing_time:.2f}s)")
            print(f"   Response size: {result['response_size_kb']} KB")
            
        else:
            result["error"] = {
                "status_code": response.status_code,
                "error_message": response.text
            }
            print(f"❌ Document Digitization - Failed! Status: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        result = {
            "endpoint": "document-digitization",
            "status_code": None,
            "processing_time_seconds": None,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": {
                "exception": str(e),
                "type": type(e).__name__
            }
        }
        print(f"❌ Document Digitization - Exception: {str(e)}")
    
    return result

def analyze_and_compare_results(layout_result: dict, digitization_result: dict) -> dict:
    """
    두 엔드포인트 결과를 분석하고 비교합니다.
    """
    comparison = {
        "comparison_timestamp": datetime.now().isoformat(),
        "test_file": str(PDF_FILE_PATH),
        "summary": {}
    }
    
    # 성공률 비교
    layout_success = layout_result.get("success", False)
    digitization_success = digitization_result.get("success", False)
    
    comparison["summary"]["success_rates"] = {
        "layout_analysis": layout_success,
        "document_digitization": digitization_success
    }
    
    # 처리 시간 비교
    if layout_success and digitization_success:
        layout_time = layout_result.get("processing_time_seconds", 0)
        digitization_time = digitization_result.get("processing_time_seconds", 0)
        
        comparison["summary"]["performance"] = {
            "layout_analysis_time": f"{layout_time}s",
            "document_digitization_time": f"{digitization_time}s",
            "faster_endpoint": "layout_analysis" if layout_time < digitization_time else "document_digitization",
            "time_difference": f"{abs(layout_time - digitization_time):.2f}s"
        }
        
        # 응답 크기 비교
        layout_size = layout_result.get("response_size_kb", 0)
        digitization_size = digitization_result.get("response_size_kb", 0)
        
        comparison["summary"]["response_sizes"] = {
            "layout_analysis_kb": layout_size,
            "document_digitization_kb": digitization_size,
            "larger_response": "layout_analysis" if layout_size > digitization_size else "document_digitization"
        }
        
        # 응답 구조 비교
        layout_keys = layout_result.get("response_keys", [])
        digitization_keys = digitization_result.get("response_keys", [])
        
        comparison["summary"]["response_structure"] = {
            "layout_analysis_keys": layout_keys,
            "document_digitization_keys": digitization_keys,
            "common_keys": list(set(layout_keys) & set(digitization_keys)) if layout_keys and digitization_keys else [],
            "unique_to_layout": list(set(layout_keys) - set(digitization_keys)) if layout_keys and digitization_keys else [],
            "unique_to_digitization": list(set(digitization_keys) - set(layout_keys)) if layout_keys and digitization_keys else []
        }
    
    # 권장사항
    if digitization_success and layout_success:
        if digitization_result.get("response_keys") and "html" in str(digitization_result.get("response_data", {})):
            comparison["recommendation"] = {
                "preferred_endpoint": "document-digitization",
                "reason": "최신 Document Parse API로 HTML/Markdown 구조화된 출력 제공, 더 고급 기능 지원"
            }
        else:
            comparison["recommendation"] = {
                "preferred_endpoint": "layout-analysis",
                "reason": "안정적인 레이아웃 분석 결과 제공"
            }
    elif digitization_success:
        comparison["recommendation"] = {
            "preferred_endpoint": "document-digitization",
            "reason": "유일하게 성공한 엔드포인트"
        }
    elif layout_success:
        comparison["recommendation"] = {
            "preferred_endpoint": "layout-analysis", 
            "reason": "유일하게 성공한 엔드포인트"
        }
    else:
        comparison["recommendation"] = {
            "preferred_endpoint": "none",
            "reason": "두 엔드포인트 모두 실패"
        }
    
    return comparison

def save_results(layout_result: dict, digitization_result: dict, comparison: dict):
    """
    결과를 JSON 파일로 저장합니다.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 개별 결과 저장
    layout_file = RESULTS_DIR / f"layout_analysis_result_{timestamp}.json"
    digitization_file = RESULTS_DIR / f"document_digitization_result_{timestamp}.json"
    comparison_file = RESULTS_DIR / f"endpoint_comparison_{timestamp}.json"
    
    with open(layout_file, "w", encoding="utf-8") as f:
        json.dump(layout_result, f, ensure_ascii=False, indent=2)
    
    with open(digitization_file, "w", encoding="utf-8") as f:
        json.dump(digitization_result, f, ensure_ascii=False, indent=2)
    
    with open(comparison_file, "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 Results saved:")
    print(f"   Layout Analysis: {layout_file}")
    print(f"   Document Digitization: {digitization_file}")  
    print(f"   Comparison: {comparison_file}")

def main():
    """
    메인 실행 함수
    """
    print("🚀 Upstage API Endpoints Comparison Test")
    print("=" * 60)
    print(f"📄 Test file: {PDF_FILE_PATH}")
    print()
    
    # 파일 존재 확인
    if not os.path.exists(PDF_FILE_PATH):
        print(f"❌ Error: PDF file not found at {PDF_FILE_PATH}")
        return
    
    # 두 엔드포인트 테스트
    layout_result = test_layout_analysis_endpoint(PDF_FILE_PATH)
    print()
    digitization_result = test_document_digitization_endpoint(PDF_FILE_PATH)
    print()
    
    # 결과 분석 및 비교
    comparison = analyze_and_compare_results(layout_result, digitization_result)
    
    # 결과 출력
    print("📊 COMPARISON SUMMARY")
    print("=" * 60)
    
    summary = comparison["summary"]
    if "performance" in summary:
        perf = summary["performance"]
        print(f"⚡ Processing Time:")
        print(f"   Layout Analysis: {perf['layout_analysis_time']}")
        print(f"   Document Digitization: {perf['document_digitization_time']}")
        print(f"   Faster: {perf['faster_endpoint']}")
        print()
    
    if "response_sizes" in summary:
        sizes = summary["response_sizes"]
        print(f"📦 Response Size:")
        print(f"   Layout Analysis: {sizes['layout_analysis_kb']} KB")
        print(f"   Document Digitization: {sizes['document_digitization_kb']} KB")
        print(f"   Larger: {sizes['larger_response']}")
        print()
    
    # 권장사항
    if "recommendation" in comparison:
        rec = comparison["recommendation"]
        print(f"💡 RECOMMENDATION:")
        print(f"   Preferred: {rec['preferred_endpoint']}")
        print(f"   Reason: {rec['reason']}")
        print()
    
    # 결과 저장
    save_results(layout_result, digitization_result, comparison)
    
    print("✅ Test completed successfully!")

if __name__ == "__main__":
    main()