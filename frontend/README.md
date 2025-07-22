# Stockreport Reader Frontend

React + TypeScript 기반의 PDF 뷰어 및 채팅 인터페이스

## 시작하기

### 개발 환경 설정

1. 환경변수 설정:
```bash
cp .env.example .env
```

`.env` 파일을 열어 API 엔드포인트를 설정합니다:
```
VITE_UPLOAD_API_URL=http://localhost:9000
VITE_QUERY_API_URL=http://localhost:8000
```

2. 의존성 설치:
```bash
pnpm install
```

3. 개발 서버 실행:
```bash
pnpm dev
```

## 주요 스크립트

```bash
pnpm dev          # 개발 서버 실행
pnpm build        # 프로덕션 빌드
pnpm preview      # 빌드 결과 미리보기
pnpm test         # 테스트 실행
pnpm test:coverage # 테스트 커버리지 확인
pnpm lint         # ESLint 실행
pnpm format       # Prettier 포맷팅
```

## 폴더 구조

```
src/
├── api/          # API 통신 모듈
│   ├── upload.ts   # PDF 업로드 API
│   ├── chunks.ts   # 청크 조회 API
│   └── chat.ts     # 채팅 SSE API
├── components/   # UI 컴포넌트
│   ├── pdf/        # PDF 관련 컴포넌트
│   ├── chat/       # 채팅 관련 컴포넌트
│   └── layout/     # 레이아웃 컴포넌트
├── store/        # 상태 관리
│   └── useAppStore.ts # Zustand 스토어
├── hooks/        # 커스텀 훅
│   ├── useChunks.ts  # 청크 데이터 페칭
│   └── useBlink.ts   # UI 효과
└── types/        # TypeScript 타입 정의
```

## 주요 기능

### PDF 뷰어
- react-pdf를 사용한 PDF 렌더링
- 페이지 네비게이션 (이전/다음)
- 줌 인/아웃 기능
- 청크 오버레이 표시 (BBox 기반)

### 청크 시스템
- 5초마다 청크 데이터 폴링
- 클릭으로 청크 인용 토글
- 인용된 청크 칩 표시

### 채팅 인터페이스
- SSE 기반 스트리밍 응답
- 메시지별 상태 관리 (sending/sent/error)
- 페이지 참조 뱃지 표시

## 테스트

테스트는 Vitest를 사용합니다:

```bash
# 단위 테스트 실행
pnpm test

# 워치 모드로 실행
pnpm vitest

# 커버리지 확인
pnpm test:coverage
```

현재 테스트 커버리지:
- Store: 100%
- Hooks: 100%
- Components: 진행 중

## 빌드 및 배포

프로덕션 빌드:
```bash
pnpm build
```

빌드 결과는 `dist/` 폴더에 생성됩니다.

## 기술 스택

- **React 19**: UI 라이브러리
- **TypeScript**: 타입 안정성
- **Vite**: 빌드 도구
- **Tailwind CSS**: 스타일링
- **Zustand**: 상태 관리
- **React-PDF**: PDF 렌더링
- **Tanstack Query**: 데이터 페칭
- **Vitest**: 테스트 프레임워크

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| VITE_UPLOAD_API_URL | 업로드 API 주소 | http://localhost:9000 |
| VITE_QUERY_API_URL | 쿼리 API 주소 | http://localhost:8000 |
