import json
import os
from tavily import TavilyClient
from google import genai
from google.genai import types
from ai.prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES

MODEL_NAME = "gemini-3-flash-preview"


def search_facts(spot_name: str) -> str:
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    result = tavily.search(
        query=f"{spot_name} 역사 문화 유래",
        search_depth="basic",
        max_results=3,
        include_answer=True,
    )
    facts = result.get("answer") or ""
    for r in result.get("results", []):
        facts += f"\n{r.get('content', '')}"
    return facts


def generate_story(spot_name: str, category: str, facts: str) -> dict:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
    )
    return response.parsed or json.loads(response.text)
