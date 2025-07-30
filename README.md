# 미래에셋 AI 리서치 어시스턴트
멀티 에이전트 기반 증권사 리포트 및 실시간 금융 데이터 통합 분석 시스템
---
**미래에셋증권 AI 페스티벌** |  AI Service 부문 [🔗](https://miraeassetfesta.com/) <br> <br>
**팀 설명해주세요.** | 강준석, 이동주, 이유진
---
## 🚀 설치 및 실행 방법

### 📋 사전 요구사항
- **Python 3.11** 이상
- **Node.js 18** 이상 
- **Conda** (Anaconda 또는 Miniconda)
- **pnpm** (Node.js 패키지 매니저)

### 1️⃣ Conda 가상환경 설정

```bash
# Conda 가상환경 생성 (Python 3.11)
conda create -n py311-base python=3.11 -y

# 가상환경 활성화
conda activate py311-base
```

### 2️⃣ Backend 설정

```bash
# 백엔드 디렉토리로 이동
cd backend

# Python 패키지 설치
pip install -r requirements.txt
```

#### 환경변수 설정
`backend/secrets/.env` 파일을 생성하고 다음 항목들을 설정하세요:

```env
# DART API 키 (전자공시시스템)
DART_API_KEY=your_dart_api_key_here

# Naver API 키
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Tavily API 키 (웹 검색)
TAVILY_API_KEY=your_tavily_api_key

# Clova API 키
CLOVA_API_KEY=your_clova_api_key

# Upstage API 키 (문서 분석)
UPSTAGE_API_KEY=your_upstage_api_key
```

#### Kiwoom REST API 설정
키움 API는 별도의 텍스트 파일로 관리됩니다:

1. **앱키 파일 생성**: `backend/secrets/{id}_appkey.txt`
```txt
your_kiwoom_app_key_here
```

2. **시크릿키 파일 생성**: `backend/secrets/{id}_secretkey.txt`
```txt
your_kiwoom_secret_key_here
```

3. **IP 화이트리스트 등록**: 
   - [키움 Open API](https://apiportal.kiwoom.com/) 사이트 로그인
   - 본인 IP 주소를 화이트리스트에 추가 (필수)
   - API 사용 승인 후 앱키/시크릿키 발급받기

4. **토큰 파일**: `access_token.json` (자동 생성)

### 3️⃣ Frontend 설정

```bash
# pnpm 설치 (전역)
npm install -g pnpm

# 프론트엔드 디렉토리로 이동
cd frontend

# 패키지 설치
pnpm install
```

#### Frontend 환경변수 설정
`frontend/.env` 파일을 생성하고 API 엔드포인트를 설정하세요:

```env
# Backend API URLs
VITE_UPLOAD_API_URL=http://localhost:9000
VITE_QUERY_API_URL=http://localhost:8000
```

> **참고**: 개발 환경에서는 기본값으로 동작하므로 `.env` 파일 생성이 선택사항입니다. 배포 환경에서는 실제 서버 URL로 변경하세요.

### 4️⃣ 실행 방법

#### 🔸 자동 실행 (Windows)
```bash
# 프로젝트 루트 디렉토리에서
start-services.bat
```

#### 🔸 수동 실행
각각의 터미널에서 다음 명령어를 실행하세요:

**터미널 1 - Upload API**
```bash
cd backend
conda activate py311-base
uvicorn upload_api:app --host 0.0.0.0 --port 9000 --reload
```

**터미널 2 - Supervisor API**
```bash
cd backend
conda activate py311-base
uvicorn agents.supervisor.api:app --host 0.0.0.0 --port 8000 --reload
```

**터미널 3 - Frontend**
```bash
cd frontend
pnpm dev
```

### 5️⃣ 서비스 접속

실행이 완료되면 다음 주소로 접속할 수 있습니다:

- **🌐 Frontend**: http://localhost:5173
- **📤 Upload API**: http://localhost:9000/docs
- **🤖 Supervisor API**: http://localhost:8000/docs