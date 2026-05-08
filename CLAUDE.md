# 동네도감 - 백엔드 & AI 파이프라인

## 프로젝트 개요
위치 기반 AI 문화 탐험 서비스 "동네도감"의 백엔드 서버 및 AI 스토리 생성 파이프라인.
사용자 위치 주변의 역사·건축·인물·예술문화 이야기를 AI로 생성해 제공한다.

## 담당 영역
- **BE**: FastAPI + Firebase Firestore 백엔드 서버
- **AI**: Gemini API 기반 스토리 생성 파이프라인 (Python 스크립트)

## 기술 스택
- Python, FastAPI, uvicorn
- Firebase Firestore (firebase-admin SDK)
- Gemini API (gemini-2.0-flash, Google AI Studio)
- Pydantic (데이터 모델)

## 프로젝트 구조 (예정)
```
server/
├── main.py                  # FastAPI 앱 진입점
├── models.py                # Pydantic 데이터 모델
├── routers/
│   └── spots.py             # /regions/{regionId}/spots 라우터
├── firebase_client.py       # Firebase 초기화 및 Firestore 클라이언트
├── ai/
│   ├── generate_stories.py  # 스토리 일괄 생성 스크립트 (AI-01~05)
│   └── prompts.py           # 시스템 프롬프트 및 few-shot 예시
├── seed.py                  # 초기 데이터 시딩 스크립트 (BE-06)
└── data/
    └── raw/                 # 원본 수집 데이터 (AI-04)
```

## Firestore 컬렉션 구조
```
regions/{regionId}/spots/{spotId}
```

### StorySpot 모델
```python
class StorySpot(BaseModel):
    id: str
    name: str
    category: str  # 역사/건축/인물/전통문화/예술문화/자연문화
    lat: float
    lng: float
    summary: str        # 1줄 미리보기
    story_past: str
    story_present: str
    story_meaning: str
    keywords: list[str]
    related_contents: list[RelatedContent]

class RelatedContent(BaseModel):
    type: str   # 책/영화/장소
    title: str
    description: str
```

## API 엔드포인트
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/regions` | 전체 지역 목록 |
| GET | `/regions/{regionId}/spots` | 지역별 스팟 목록 |
| GET | `/regions/{regionId}/spots/{spotId}` | 스팟 상세 |
| POST | `/regions/{regionId}/spots` | 스팟 추가 (AI Agent용, X-API-Key 인증) |

## 백로그 (담당)
- **BE-01**: FastAPI 프로젝트 세팅 + Firebase 연결
- **BE-02**: 데이터 모델 정의 (Pydantic + Firestore 구조)
- **BE-03**: GET /spots 목록 API
- **BE-04**: GET /spots/{id} 상세 API
- **BE-05**: POST /spots 추가 API (AI Agent용, X-API-Key 인증)
- **BE-06**: 초기 데이터 시딩 스크립트
- **AI-01**: 스토리 생성 파이프라인 설계
- **AI-02**: 스토리 이야기체 재구성 프롬프트 작성 (few-shot 포함)
- **AI-03**: 키워드 추출 및 관련 콘텐츠 매핑 (Should)
- **AI-04**: 원본 데이터 수집 (성수·제주·서울 각 5개 스팟)
- **AI-05**: 전체 스팟 일괄 생성 실행 및 검수

## Git 컨벤션
- **브랜치명**: `feat/{작업명}` (예: `feat/be-01-fastapi-setup`)
- **이슈 형태**: `[BE-00] 작업명`
  - 내용 구성: 배경 / 작업범위 / 완료기준 / 관련
- **커밋 메시지**: 한국어로 작성
  - 예: `feat: GET /spots 엔드포인트 구현`
  - Co-authored-by 트레일러 금지
- **PR**: 각 태스크 완료 시 생성

## 서버 실행
```bash
uvicorn main:app --reload
```

## 데이터 시딩
```bash
python seed.py
```

## AI 스토리 생성
```bash
python ai/generate_stories.py
```

## AI 라이브러리
```bash
pip install google-generativeai
```

## 환경변수
- `GEMINI_API_KEY`: Google AI Studio에서 발급한 Gemini API 키
- `FIREBASE_CREDENTIALS`: Firebase 서비스 계정 키 경로
- `API_KEY`: POST /spots 엔드포인트 인증 키

## 협업 규칙
- BE/AI 완료 기준: 로컬 테스트 통과 + Firestore 저장 확인
- 1차 통합 체크포인트(T+5:30): Gemini API로 스토리 1개 생성 확인
- 2차 통합 체크포인트(T+9:30): 15개 스팟 Firestore 저장 완료
