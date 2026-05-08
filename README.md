# 동네도감 - 백엔드 & AI 파이프라인

위치 기반 AI 문화 탐험 서비스 **동네도감**의 백엔드 서버 및 AI 스토리 생성 파이프라인입니다.
일상 속에서 무심코 지나치는 장소들의 숨겨진 이야기(지명 유래, 역사적 사건, 비하인드 스토리)를 AI로 생성해 제공합니다.

## 기술 스택

- **Backend**: Python, FastAPI, uvicorn
- **Database**: Firebase Firestore (firebase-admin SDK)
- **AI**: Gemini API (google-genai)
- **Search**: Tavily API
- **Image**: Wikimedia Commons API (한국어 위키피디아)
- **Validation**: Pydantic v2

## 프로젝트 구조

```
server/
├── main.py                  # FastAPI 앱 진입점
├── models.py                # Pydantic 데이터 모델
├── firebase_client.py       # Firestore 클라이언트 (싱글톤)
├── requirements.txt
├── routers/
│   └── spots.py             # API 라우터
├── ai/
│   ├── generate_stories.py  # 스팟 일괄 생성 스크립트
│   ├── story_service.py     # Tavily 검색 + Gemini 생성 핵심 로직
│   └── prompts.py           # 시스템 프롬프트 및 few-shot 예시
└── data/
    └── raw/                 # 원본 수집 데이터
```

## 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하세요.

```env
GEMINI_API_KEY=...        # Google AI Studio에서 발급
TAVILY_API_KEY=...        # Tavily에서 발급
FIREBASE_CREDENTIALS=firebase-credentials.json
API_KEY=...               # POST 엔드포인트 인증 키 (임의 설정)
API_BASE_URL=http://localhost:8000  # 선택사항, 기본값 http://localhost:8000
```

Firebase 서비스 계정 키(`firebase-credentials.json`)는 Firebase 콘솔 → 프로젝트 설정 → 서비스 계정에서 발급합니다.

## 설치 및 실행

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload
```

서버 실행 후 `http://localhost:8000/docs`에서 Swagger UI로 API를 테스트할 수 있습니다.

## API 엔드포인트

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/regions` | 전체 지역 목록 | - |
| GET | `/regions/{region_id}/spots` | 지역별 스팟 목록 (요약) | - |
| GET | `/regions/{region_id}/spots/{spot_id}` | 스팟 상세 | - |
| POST | `/regions/{region_id}/generate` | 지역명 기반 스팟 자동 탐색 및 스토리 일괄 생성 | X-API-Key |
| POST | `/regions/{region_id}/spots/{spot_id}/generate` | 단일 스팟 온디맨드 스토리 생성 | X-API-Key |
| POST | `/regions/{region_id}/spots` | 스팟 직접 추가 | X-API-Key |

인증이 필요한 엔드포인트는 요청 헤더에 `x-api-key: {API_KEY}`를 포함해야 합니다.

## AI 스토리 생성 파이프라인

### 데이터 모델 (Firestore)

```
regions/{region_id}/spots/{spot_id}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | str | 스팟 ID (예: `jongno_01`) |
| `name` | str | 장소명 |
| `category` | str | 역사/건축/인물/전통문화/예술문화/자연문화 |
| `lat`, `lng` | float | 좌표 |
| `summary` | str | 1줄 미리보기 |
| `story_past` | str | 과거 이야기 |
| `story_present` | str | 현재 모습 |
| `story_meaning` | str | 문화적 의미 |
| `keywords` | list[str] | 키워드 |
| `related_contents` | list | 관련 콘텐츠 (책/영화/장소) |
| `sources` | list[str] | 출처 URL 목록 |
| `image_url` | str | 위키피디아 대표 이미지 URL |

### 생성 흐름

**방법 1 — 일괄 생성 스크립트**
```bash
python ai/generate_stories.py
```
`SPOTS` 리스트에 정의된 스팟을 순차적으로 처리합니다.

**방법 2 — 지역 자동 탐색 API**
```bash
curl -X POST http://localhost:8000/regions/jongno/generate \
  -H "x-api-key: {API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"region_name": "종로"}'
```
지역명만 입력하면 Tavily로 일상 공간 탐색 → Gemini로 스팟 목록 추출 → 각 스팟 스토리 생성 → Firestore 저장까지 자동 처리합니다. 스팟은 병렬로 처리됩니다.

**방법 3 — 단일 스팟 온디맨드 생성**
```bash
curl -X POST http://localhost:8000/regions/jongno/spots/jongno_01/generate \
  -H "x-api-key: {API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"name": "피맛골", "category": "역사", "lat": 37.5700, "lng": 126.9822}'
```
특정 스팟의 스토리를 재생성하거나 새로 추가할 때 사용합니다. 동일한 `spot_id`로 호출하면 덮어씁니다.
