import json
import os
from pydantic import BaseModel
from tavily import TavilyClient
from google import genai
from google.genai import types
from ai.prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES


class SpotInfo(BaseModel):
    id: str
    name: str
    category: str
    lat: float
    lng: float


class _SpotListSchema(BaseModel):
    spots: list[SpotInfo]


class _RelatedContent(BaseModel):
    type: str
    title: str
    description: str


class _StorySchema(BaseModel):
    summary: str
    story_past: str
    story_present: str
    story_meaning: str
    keywords: list[str]
    related_contents: list[_RelatedContent]

MODEL_NAME = "gemini-2.5-flash-preview-05-20"

_tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
_genai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def search_facts(spot_name: str) -> tuple[str, list[str]]:
    result = _tavily.search(
        query=f"{spot_name} 지명 유래 역사적 사건 비하인드 스토리 과거",
        search_depth="advanced",
        max_results=5,
        include_answer=True,
    )
    facts = result.get("answer") or ""
    sources = []
    for r in result.get("results", []):
        facts += f"\n{r.get('content', '')}"
        if url := r.get("url"):
            sources.append(url)
    return facts, sources


def generate_story(spot_name: str, category: str, facts: str) -> dict:
    contents = []
    for msg in FEW_SHOT_EXAMPLES:
        contents.append(types.Content(role=msg["role"], parts=[types.Part(text=msg["parts"][0])]))

    user_prompt = f"""장소명: {spot_name}
카테고리: {category}
수집된 사실: {facts}

위 사실을 바탕으로 아래 JSON 형식으로 작성하세요:
{{
  "summary": "1줄 미리보기 (30자 이내)",
  "story_past": "과거 이야기 (2~3문장)",
  "story_present": "현재 모습 (2~3문장)",
  "story_meaning": "문화적 의미 (2~3문장)",
  "keywords": ["키워드1", "키워드2", "키워드3"],
  "related_contents": [{{"type": "책/영화/장소", "title": "제목", "description": "한 줄 설명"}}]
}}"""
    contents.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))

    response = _genai.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=_StorySchema,
        ),
    )
    return response.parsed.model_dump() if response.parsed else json.loads(response.text)


def discover_spots(region_id: str, region_name: str) -> list[SpotInfo]:
    result = _tavily.search(
        query=f"{region_name} 지명 유래 골목 역사 숨겨진 이야기 과거 흔적",
        search_depth="advanced",
        max_results=10,
        include_answer=True,
    )
    raw = result.get("answer") or ""
    for r in result.get("results", []):
        raw += f"\n{r.get('content', '')}"

    prompt = f"""아래는 {region_name} 지역의 역사·지명 유래 관련 검색 결과입니다.
이 내용을 바탕으로 일상 속에서 지나치기 쉽지만 흥미로운 역사나 이야기가 있는 장소를 5개 추출하세요.
유명 관광지보다는 골목, 시장, 다리, 공터 등 평범한 일상 공간을 우선으로 선택하세요.

검색 결과:
{raw}

각 장소의 id는 "{region_id}_01", "{region_id}_02" 형식으로 지정하세요.
category는 역사/건축/인물/전통문화/예술문화/자연문화 중 하나로 지정하세요.
lat, lng는 실제 좌표를 최대한 정확하게 입력하세요."""

    response = _genai.models.generate_content(
        model=MODEL_NAME,
        contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_SpotListSchema,
        ),
    )
    try:
        parsed = response.parsed if response.parsed else _SpotListSchema(**json.loads(response.text))
        return parsed.spots
    except Exception:
        return []
