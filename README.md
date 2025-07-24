# Stockreport Reader

증권사 리포트 PDF를 업로드하고, 문단 단위로 인용하며 대화할 수 있는 AI 챗봇 서비스입니다.

## 프로젝트 구조

```
Stockreport-reader/
├── backend/
│   ├── main_supervisor.py      # 멀티에이전트 시스템 (포트 8000)
│   ├── upload_api.py          # PDF 업로드 서비스 (포트 9000)
│   └── agents/                # 멀티에이전트 모듈
└── frontend/                  # React 웹 애플리케이션
    ├── src/
    │   ├── api/              # API 통신 모듈
    │   ├── components/       # UI 컴포넌트
    │   ├── store/           # 상태 관리 (Zustand)
    │   ├── hooks/           # 커스텀 훅
    │   └── types/           # TypeScript 타입 정의
    └── public/
```

## 주요 기능

### 1. PDF 업로드 및 뷰어
- PDF 파일 드래그 앤 드롭 업로드
- React-PDF 기반 PDF 렌더링
- 페이지 네비게이션 및 줌 기능

### 2. 청크 기반 인용 시스템
- PDF 문단별 BBox(Bounding Box) 표시
- 클릭으로 문단 인용 선택/해제
- 인용된 청크는 채팅 시 자동으로 컨텍스트에 포함

### 3. AI 채팅 인터페이스
- ChatClovaX 기반 대화형 AI
- SSE(Server-Sent Events) 스트리밍 응답
- 답변에 참조 페이지 표시

## 설치 및 실행

### 사전 요구사항
- Python 3.8+
- Node.js 18+
- pnpm

### Backend 설정

1. 가상환경 생성 및 활성화:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. 환경변수 설정 (secrets/.env):
```
CLOVASTUDIO_API_KEY=your_api_key_here
LANGSMITH_API_KEY=your_api_key_here
```

(frontend/.env)
```
VITE_UPLOAD_API_URL=http://localhost:9000
VITE_QUERY_API_URL=http://localhost:8000
```

4. 서비스 실행:
```bash
# Upload API (포트 9000)
cd backend && conda activate py311-base && uvicorn upload_api:app --host 0.0.0.0 --port 9000 --reload

# Supervisor API (포트 8000)
cd backend && conda activate py311-base && uvicorn agents.supervisor.api:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && pnpm dev
```
or just run `start-services.bat`

### Frontend 설정

1. 의존성 설치:
```bash
cd frontend
pnpm install
```

2. 개발 서버 실행:
```bash
pnpm dev
```

3. 브라우저에서 http://localhost:5173 접속

## API 명세

### Upload Service (포트 9000)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /upload | PDF 파일 업로드 |
| GET | /chunks/{fileId} | 청크 정보 조회 |
| GET | /file/{fileId}/download | PDF 파일 다운로드 |

### Query Service (포트 8000)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /query | AI 질의 (SSE 스트리밍) |
| GET | /health | 서비스 상태 확인 |

## 작동 방식

### BBox 없는 상태 (초기)
1. PDF 업로드 시 `processed_states.json` 생성 (빈 상태)
2. 프론트엔드는 PDF만 렌더링, 인용 UI 비활성화
3. `/chunks/{fileId}` API는 빈 배열 반환

### BBox 있는 상태 (청킹 완료 후)
1. 백그라운드 파이프라인이 청킹 및 BBox 추출
2. `processed_states.json`에 `chunks_content` 업데이트
3. `/chunks/{fileId}` API가 BBox 정보 반환
4. 프론트엔드가 자동으로 오버레이 UI 활성화

## 테스트

### Frontend 테스트
```bash
cd frontend
pnpm test              # 테스트 실행
pnpm test:coverage     # 커버리지 포함
```

### Backend 테스트
```bash
cd backend
pytest                 # 테스트 실행
pytest --cov          # 커버리지 포함
```

## 기술 스택

### Backend
- FastAPI: 웹 프레임워크
- LangChain/LangGraph: 멀티에이전트 시스템
- ChatClovaX: AI 언어 모델
- PyPDF2: PDF 처리

### Frontend
- React 19 + TypeScript
- Vite: 빌드 도구
- Tailwind CSS: 스타일링
- Zustand: 상태 관리
- React-PDF: PDF 렌더링
- Tanstack Query: 데이터 페칭
- Vitest: 테스트 프레임워크

## 확장성

이 프로젝트는 다음과 같은 확장이 가능하도록 설계되었습니다:

1. **청킹 파이프라인 추가**: 백그라운드에서 PDF 분석 및 BBox 추출
2. **벡터 DB 통합**: 청크별 임베딩 및 RAG 구현
3. **다중 파일 지원**: 여러 PDF 동시 관리
4. **사용자 인증**: 세션 기반 파일 관리

## 라이선스

MIT License
