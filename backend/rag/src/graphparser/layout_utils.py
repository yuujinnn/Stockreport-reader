import os
import json
import pickle
import requests
import pymupdf
import tiktoken
import math
from PIL import Image


class LayoutAnalyzer:
    def __init__(self, api_key):
        """
        LayoutAnalyzer 클래스의 생성자

        :param api_key: Upstage API 인증을 위한 API 키
        """
        self.api_key = api_key

    def _upstage_layout_analysis(self, input_file):
        """
        Upstage의 최신 Document Parse API (document-digitization)를 호출하여 문서 분석을 수행합니다.
        응답은 기존 layout-analysis 형식과 호환되도록 변환됩니다.

        :param input_file: 분석할 PDF 파일의 경로
        :return: 분석 결과가 저장된 JSON 파일의 경로
        """
        # API 요청 헤더 설정
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # API 요청 데이터 설정 (최신 Document Parse API 파라미터)
        data = {
            "model": "document-parse",
            "ocr": "force",  # OCR 강제 실행
            "chart_recognition": True,
            "coordinates": True,
            "output_formats": '["html", "markdown"]',
        }

        # 분석할 PDF 파일 열기
        files = {"document": open(input_file, "rb")}

        # API 요청 보내기 (새로운 document-digitization 엔드포인트 사용)
        response = requests.post(
            "https://api.upstage.ai/v1/document-digitization",
            headers=headers,
            data=data,
            files=files,
        )

        # API 응답 처리 및 결과 저장
        if response.status_code == 200:
            # 새 API 응답을 구 형식으로 변환
            new_response = response.json()
            legacy_response = self._convert_to_legacy_format(new_response)
            
            # 분석 결과를 저장할 JSON 파일 경로 생성
            output_file = os.path.splitext(input_file)[0] + ".json"

            # 변환된 분석 결과를 JSON 파일로 저장
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(legacy_response, f, ensure_ascii=False)

            return output_file
        else:
            # API 요청이 실패한 경우 예외 발생
            raise ValueError(f"API 요청 실패. 상태 코드: {response.status_code}, 응답: {response.text}")

    def _convert_to_legacy_format(self, new_response):
        """
        새로운 document-digitization API 응답을 기존 layout-analysis 형식으로 변환합니다.
        
        :param new_response: 새 API 응답 JSON
        :return: 구 형식으로 변환된 JSON
        """
        # PDF 페이지 크기 정보 가져오기 (PyMuPDF를 사용해서 실제 페이지 크기 추출)
        pdf_metadata = self._extract_pdf_metadata()
        
        # 기본 구조 생성
        legacy_response = {
            "api": "2.0",
            "billed_pages": new_response.get("usage", {}).get("pages", 1),
            "elements": [],
            "html": new_response.get("content", {}).get("html", ""),
            "metadata": pdf_metadata,
            "mimetype": "multipart/form-data",  # 구 버전과 동일한 값
            "model": new_response.get("model", "document-parse"),
            "text": new_response.get("content", {}).get("text", "")
        }
        
        # elements 변환
        for element in new_response.get("elements", []):
            legacy_element = self._convert_element_to_legacy(element, pdf_metadata)
            legacy_response["elements"].append(legacy_element)
        
        return legacy_response
    
    def _extract_pdf_metadata(self):
        """
        현재 처리 중인 PDF 파일에서 페이지 크기 정보를 추출합니다.
        
        :return: 페이지 메타데이터
        """
        if not hasattr(self, 'current_pdf_file') or not self.current_pdf_file:
            # 기본값 반환 (A4 기준 DPI 150)
            return {
                "pages": [
                    {"height": 1754, "page": 1, "width": 1241},
                    {"height": 1754, "page": 2, "width": 1241}
                ]
            }
        
        try:
            # PyMuPDF를 사용해서 실제 PDF 페이지 크기 추출
            pages_metadata = []
            
            with pymupdf.open(self.current_pdf_file) as doc:
                for page_num, page in enumerate(doc, 1):
                    # 페이지 크기를 150 DPI 기준으로 픽셀 단위로 변환
                    # (구 API가 150 DPI 기준으로 좌표를 제공했던 것으로 보임)
                    rect = page.rect
                    dpi = 150
                    width = int(rect.width * dpi / 72)  # 72 DPI가 기본
                    height = int(rect.height * dpi / 72)
                    
                    pages_metadata.append({
                        "height": height,
                        "page": page_num,
                        "width": width
                    })
            
            return {"pages": pages_metadata}
            
        except Exception as e:
            print(f"⚠️ PDF 메타데이터 추출 실패: {e}")
            # 오류 발생 시 기본값 반환
            return {
                "pages": [
                    {"height": 1754, "page": 1, "width": 1241},
                    {"height": 1754, "page": 2, "width": 1241}
                ]
            }
    
    def _convert_element_to_legacy(self, element, pdf_metadata):
        """
        개별 element를 구 형식으로 변환합니다.
        
        :param element: 새 API의 element
        :param pdf_metadata: PDF 메타데이터 (페이지 크기 정보)
        :return: 구 형식의 element
        """
        page_num = element.get("page", 1)
        page_info = None
        
        # 해당 페이지의 크기 정보 찾기
        for page_meta in pdf_metadata.get("pages", []):
            if page_meta["page"] == page_num:
                page_info = page_meta
                break
        
        # 페이지 정보가 없으면 기본값 사용
        if not page_info:
            page_info = {"width": 1241, "height": 1754}
        
        # 상대좌표를 절대좌표로 변환
        bounding_box = []
        for coord in element.get("coordinates", []):
            abs_x = int(coord["x"] * page_info["width"])
            abs_y = int(coord["y"] * page_info["height"])
            bounding_box.append({"x": abs_x, "y": abs_y})
        
        # 구 형식 element 생성
        legacy_element = {
            "bounding_box": bounding_box,
            "category": element.get("category", ""),
            "html": element.get("content", {}).get("html", ""),
            "id": element.get("id", 0),
            "page": page_num,
            "text": element.get("content", {}).get("text", "")
        }
        
        return legacy_element

    def execute(self, input_file):
        """
        주어진 입력 파일에 대해 레이아웃 분석을 실행합니다.

        :param input_file: 분석할 PDF 파일의 경로
        :return: 분석 결과가 저장된 JSON 파일의 경로
        """
        # PDF 파일 경로를 인스턴스 변수로 저장 (메타데이터 추출용)
        self.current_pdf_file = input_file
        return self._upstage_layout_analysis(input_file)


class ImageCropper:
    @staticmethod
    def pdf_to_image(pdf_file, page_num, dpi=300):
        """
        PDF 파일의 특정 페이지를 이미지로 변환하는 메서드

        :param page_num: 변환할 페이지 번호 (1부터 시작)
        :param dpi: 이미지 해상도 (기본값: 300)
        :return: 변환된 이미지 객체
        """
        with pymupdf.open(pdf_file) as doc:
            page = doc[page_num].get_pixmap(dpi=dpi)
            target_page_size = [page.width, page.height]
            page_img = Image.frombytes("RGB", target_page_size, page.samples)
        return page_img

    @staticmethod
    def normalize_coordinates(coordinates, output_page_size):
        """
        좌표를 정규화하는 정적 메서드

        :param coordinates: 원본 좌표 리스트
        :param output_page_size: 출력 페이지 크기 [너비, 높이]
        :return: 정규화된 좌표 (x1, y1, x2, y2)
        """
        x_values = [coord["x"] for coord in coordinates]
        y_values = [coord["y"] for coord in coordinates]
        x1, y1, x2, y2 = min(x_values), min(y_values), max(x_values), max(y_values)

        return (
            x1 / output_page_size[0],
            y1 / output_page_size[1],
            x2 / output_page_size[0],
            y2 / output_page_size[1],
        )

    @staticmethod
    def crop_image(img, coordinates, output_file):
        """
        이미지를 주어진 좌표에 따라 자르고 ChatClovaX HCX-005 제약사항에 맞게 조정하여 저장하는 정적 메서드
        
        ChatClovaX HCX-005 제약사항:
        - 가로, 세로 중 긴 쪽: 2240px 이하
        - 짧은 쪽: 4px 이상  
        - 가로:세로 비율: 1:5 또는 5:1 이하

        :param img: 원본 이미지 객체
        :param coordinates: 정규화된 좌표 (x1, y1, x2, y2)
        :param output_file: 저장할 파일 경로
        """
        img_width, img_height = img.size
        x1, y1, x2, y2 = [
            int(coord * dim)
            for coord, dim in zip(coordinates, [img_width, img_height] * 2)
        ]
        cropped_img = img.crop((x1, y1, x2, y2))
        
        # ChatClovaX HCX-005 제약사항에 맞게 이미지 조정
        adjusted_img = ImageCropper._adjust_image_for_clovax(cropped_img)
        adjusted_img.save(output_file)

    @staticmethod
    def _adjust_image_for_clovax(img):
        """
        ChatClovaX HCX-005 제약사항에 맞게 이미지를 조정하는 메서드
        
        :param img: PIL Image 객체
        :return: 조정된 PIL Image 객체
        """
        original_width, original_height = img.size
        print(f"🖼️  Original image size: {original_width}x{original_height}")
        print(f"🔢 Original aspect ratio: {max(original_width, original_height) / min(original_width, original_height):.2f}:1")
        
        width, height = original_width, original_height
        
        # 1. 비율 제한 먼저 처리: 1:5 또는 5:1을 넘으면 흰색 배경으로 패딩 추가
        aspect_ratio = max(width, height) / min(width, height)
        max_aspect_ratio = 4.9  # 5.0보다 여유있게 설정 (부동소수점 오차 방지)
        
        if aspect_ratio > max_aspect_ratio:
            print(f"⚠️  Aspect ratio {aspect_ratio:.3f}:1 exceeds limit {max_aspect_ratio}:1")
            
            if width > height:
                # 가로가 긴 경우: 세로에 패딩 추가 (올림 처리로 확실히 제약사항 만족)
                target_height = math.ceil(width / max_aspect_ratio)
                padding_height = target_height - height
                
                # 흰색 배경으로 새 이미지 생성
                new_img = Image.new('RGB', (width, target_height), 'white')
                # 기존 이미지를 중앙에 배치
                paste_y = padding_height // 2
                new_img.paste(img, (0, paste_y))
                
                img = new_img
                width, height = width, target_height
                new_ratio = width / height
                print(f"📐 Aspect ratio adjusted: {original_width}x{original_height} → {width}x{height}")
                print(f"🔢 New aspect ratio: {new_ratio:.3f}:1")
                
            else:
                # 세로가 긴 경우: 가로에 패딩 추가 (올림 처리로 확실히 제약사항 만족)
                target_width = math.ceil(height / max_aspect_ratio)
                padding_width = target_width - width
                
                # 흰색 배경으로 새 이미지 생성
                new_img = Image.new('RGB', (target_width, height), 'white')
                # 기존 이미지를 중앙에 배치
                paste_x = padding_width // 2
                new_img.paste(img, (paste_x, 0))
                
                img = new_img
                width, height = target_width, height
                new_ratio = height / width
                print(f"📐 Aspect ratio adjusted: {original_width}x{original_height} → {width}x{height}")
                print(f"🔢 New aspect ratio: 1:{new_ratio:.3f}")
        
        # 2. 크기 제한: 긴 쪽이 2240px를 넘으면 비율 유지하며 축소
        max_dimension = 2240
        if max(width, height) > max_dimension:
            print(f"⚠️  Max dimension {max(width, height)}px exceeds limit {max_dimension}px")
            
            if width > height:
                new_width = max_dimension
                new_height = int((height * max_dimension) / width)
            else:
                new_height = max_dimension
                new_width = int((width * max_dimension) / height)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            width, height = new_width, new_height
            print(f"📏 Image resized to {width}x{height} (max dimension: {max_dimension}px)")
        
        # 3. 최소 크기 확인: 짧은 쪽이 4px 미만이면 4px로 조정
        min_dimension = 4
        if min(width, height) < min_dimension:
            print(f"⚠️  Min dimension {min(width, height)}px below limit {min_dimension}px")
            
            if width < height:
                new_width = min_dimension
                new_height = int((height * min_dimension) / width)
            else:
                new_height = min_dimension
                new_width = int((width * min_dimension) / height)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
            width, height = new_width, new_height
            print(f"📏 Image resized to {width}x{height} (min dimension: {min_dimension}px)")
        
        # 4. 최종 검증 및 안전 조정
        final_aspect_ratio = max(width, height) / min(width, height)
        print(f"✅ Final image size: {width}x{height}")
        print(f"✅ Final aspect ratio: {final_aspect_ratio:.3f}:1")
        
        # 안전 검증: 혹시 여전히 5.0을 넘는다면 한 번 더 조정
        strict_max_ratio = 5.0
        if final_aspect_ratio > strict_max_ratio:
            print(f"🚨 CRITICAL: Final ratio {final_aspect_ratio:.3f}:1 still exceeds 5.0:1!")
            print(f"🔧 Applying emergency adjustment...")
            
            if width > height:
                # 가로가 긴 경우: 세로를 더 늘림
                emergency_height = math.ceil(width / 4.95)  # 더 보수적으로
                emergency_img = Image.new('RGB', (width, emergency_height), 'white')
                paste_y = (emergency_height - height) // 2
                emergency_img.paste(img, (0, paste_y))
                img = emergency_img
                width, height = width, emergency_height
            else:
                # 세로가 긴 경우: 가로를 더 늘림
                emergency_width = math.ceil(height / 4.95)  # 더 보수적으로
                emergency_img = Image.new('RGB', (emergency_width, height), 'white')
                paste_x = (emergency_width - width) // 2
                emergency_img.paste(img, (paste_x, 0))
                img = emergency_img
                width, height = emergency_width, height
            
            final_aspect_ratio = max(width, height) / min(width, height)
            print(f"🔧 Emergency adjustment complete: {width}x{height}")
            print(f"🔢 Emergency aspect ratio: {final_aspect_ratio:.3f}:1")
        
        # ChatClovaX 제약사항 최종 검증
        max_check = max(width, height) <= 2240
        min_check = min(width, height) >= 4
        ratio_check = final_aspect_ratio <= 5.0
        
        if max_check and min_check and ratio_check:
            print(f"🎉 Image meets all ChatClovaX HCX-005 constraints!")
        else:
            print(f"❌ CRITICAL ERROR: Image STILL does not meet constraints!")
            print(f"   Max dimension: {max(width, height)} ≤ 2240? {max_check}")
            print(f"   Min dimension: {min(width, height)} ≥ 4? {min_check}")
            print(f"   Aspect ratio: {final_aspect_ratio:.3f} ≤ 5.0? {ratio_check}")
            # 이 경우 강제로 5:1 비율로 맞춤
            if not ratio_check:
                print(f"🚨 FORCING 5:1 ratio...")
                if width > height:
                    force_height = math.ceil(width / 5.0) + 1  # +1 for safety
                    force_img = Image.new('RGB', (width, force_height), 'white')
                    paste_y = (force_height - height) // 2
                    force_img.paste(img, (0, paste_y))
                    img = force_img
                    print(f"🔧 FORCED to {width}x{force_height}")
                else:
                    force_width = math.ceil(height / 5.0) + 1  # +1 for safety
                    force_img = Image.new('RGB', (force_width, height), 'white')
                    paste_x = (force_width - width) // 2
                    force_img.paste(img, (paste_x, 0))
                    img = force_img
                    print(f"🔧 FORCED to {force_width}x{height}")
        
        return img


def save_state(state, filepath):
    """상태를 pickle 파일로 저장합니다."""
    base, _ = os.path.splitext(filepath)
    with open(f"{base}.pkl", "wb") as f:
        pickle.dump(state, f)


def load_state(filepath):
    """pickle 파일에서 상태를 불러옵니다."""
    base, _ = os.path.splitext(filepath)
    with open(f"{base}.pkl", "rb") as f:
        return pickle.load(f)



