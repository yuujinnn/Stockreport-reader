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
        Upstage의 레이아웃 분석 API를 호출하여 문서 분석을 수행합니다.

        :param input_file: 분석할 PDF 파일의 경로
        :return: 분석 결과가 저장된 JSON 파일의 경로
        """
        # API 요청 헤더 설정
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # API 요청 데이터 설정 (OCR 비활성화)
        data = {"ocr": False}

        # 분석할 PDF 파일 열기
        files = {"document": open(input_file, "rb")}

        # API 요청 보내기
        response = requests.post(
            "https://api.upstage.ai/v1/document-digitization",
            headers=headers,
            data=data,
            files=files,
        )

        # API 응답 처리 및 결과 저장
        if response.status_code == 200:
            # 분석 결과를 저장할 JSON 파일 경로 생성
            output_file = os.path.splitext(input_file)[0] + ".json"

            # 분석 결과를 JSON 파일로 저장
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, ensure_ascii=False)

            return output_file
        else:
            # API 요청이 실패한 경우 예외 발생
            raise ValueError(f"API 요청 실패. 상태 코드: {response.status_code}")

    def execute(self, input_file):
        """
        주어진 입력 파일에 대해 레이아웃 분석을 실행합니다.

        :param input_file: 분석할 PDF 파일의 경로
        :return: 분석 결과가 저장된 JSON 파일의 경로
        """
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



