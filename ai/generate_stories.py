import os
import sys
import json
import time
import requests
from dotenv import load_dotenv
from tavily import TavilyClient
from google import genai
from google.genai import types

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai.prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES

load_dotenv()

SPOTS = [
    {"region_id": "seongsu", "id": "seongsu_01", "name": "성수 수제화 거리", "category": "자연문화", "lat": 37.5443, "lng": 127.0557},
    {"region_id": "seongsu", "id": "seongsu_02", "name": "서울숲", "category": "자연문화", "lat": 37.5445, "lng": 127.0374},
    {"region_id": "seongsu", "id": "seongsu_03", "name": "뚝섬 유원지", "category": "역사", "lat": 37.5300, "lng": 127.0653},
    {"region_id": "seongsu", "id": "seongsu_04", "name": "성수동 카페거리", "category": "예술문화", "lat": 37.5440, "lng": 127.0559},
    {"region_id": "seongsu", "id": "seongsu_05", "name": "건국대학교 일감호", "category": "건축", "lat": 37.5412, "lng": 127.0792},
    {"region_id": "jeju",    "id": "jeju_01",    "name": "제주 관덕정", "category": "역사", "lat": 33.5100, "lng": 126.5211},
    {"region_id": "jeju",    "id": "jeju_02",    "name": "제주 동문시장", "category": "전통문화", "lat": 33.5138, "lng": 126.5292},
    {"region_id": "jeju",    "id": "jeju_03",    "name": "산지천 갤러리", "category": "예술문화", "lat": 33.5145, "lng": 126.5238},
    {"region_id": "jeju",    "id": "jeju_04",    "name": "제주목 관아", "category": "역사", "lat": 33.5102, "lng": 126.5197},
    {"region_id": "jeju",    "id": "jeju_05",    "name": "칠성로 거리", "category": "전통문화", "lat": 33.5147, "lng": 126.5261},
    {"region_id": "jongno",  "id": "jongno_01",  "name": "인사동 거리", "category": "전통문화", "lat": 37.5742, "lng": 126.9849},
    {"region_id": "jongno",  "id": "jongno_02",  "name": "낙원상가", "category": "역사", "lat": 37.5741, "lng": 126.9843},
    {"region_id": "jongno",  "id": "jongno_03",  "name": "피맛골", "category": "역사", "lat": 37.5700, "lng": 126.9822},
    {"region_id": "jongno",  "id": "jongno_04",  "name": "운현궁", "category": "역사", "lat": 37.5752, "lng": 126.9852},
    {"region_id": "jongno",  "id": "jongno_05",  "name": "탑골공원", "category": "역사", "lat": 37.5722, "lng": 126.9872},
]

API_BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY")
MODEL_NAME = "gemini-3-flash-preview"


def search_facts(tavily: TavilyClient, spot_name: str) -> str:
    result = tavily.search(
        query=f"{spot_name} 역사 문화 유래",
        search_depth="basic",
        max_results=3,
        include_answer=True,
    )
    facts = result.get("answer") or ""
    for r in result.get("results", []):
        facts += f"\n{r.get('content', '')}"
    return facts[:2000]


def build_contents(spot: dict, facts: str) -> list:
    contents = []
    for msg in FEW_SHOT_EXAMPLES:
        role = msg["role"]
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["parts"][0])]))

    user_prompt = f"""장소명: {spot['name']}
카테고리: {spot['category']}
수집된 사실: {facts}

위 사실을 바탕으로 아래 JSON 형식으로 작성하세요:
{{
  "summary": "1줄 미리보기 (30자 이내)",
  "story_past": "과거 이야기 (2~3문장)",
  "story_present": "현재 모습 (2~3문장)",
  "story_meaning": "문화적 의미 (2~3문장)",
  "keywords": ["키워드1", "키워드2", "키워드3"],
  "related_contents": [{{"type": "책/영화/장소", "title": "제목", "description": "한 줄 설명"}}]
}}
JSON만 출력하세요. 마크다운 코드블록 없이."""
    contents.append(types.Content(role="user", parts=[types.Part(text=user_prompt)]))
    return contents


def generate_story(client: genai.Client, spot: dict, facts: str) -> dict:
    contents = build_contents(spot, facts)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def save_spot(spot: dict, story: dict):
    payload = {
        "id": spot["id"],
        "name": spot["name"],
        "category": spot["category"],
        "lat": spot["lat"],
        "lng": spot["lng"],
        **story,
    }
    res = requests.post(
        f"{API_BASE_URL}/regions/{spot['region_id']}/spots",
        json=payload,
        headers={"x-api-key": API_KEY},
    )
    res.raise_for_status()
    return res.json()


def main():
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    success, failed = 0, []

    for spot in SPOTS:
        print(f"[{spot['id']}] {spot['name']} 처리 중...")
        try:
            facts = search_facts(tavily, spot["name"])
            story = generate_story(client, spot, facts)
            save_spot(spot, story)
            print(f"  ✓ 저장 완료")
            success += 1
        except Exception as e:
            print(f"  ✗ 실패: {e}")
            failed.append(spot["id"])
        time.sleep(2)

    print(f"\n완료: {success}개 성공 / {len(failed)}개 실패")
    if failed:
        print(f"실패 목록: {failed}")


if __name__ == "__main__":
    main()
