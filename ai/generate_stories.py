import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai.story_service import search_facts, generate_story

SPOTS = [
    {"region_id": "seongsu", "id": "seongsu_01", "name": "성수 수제화 거리", "category": "전통문화", "lat": 37.5443, "lng": 127.0557},
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

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")


def save_spot(spot: dict, story: dict, sources: list):
    payload = {
        "id": spot["id"],
        "name": spot["name"],
        "category": spot["category"],
        "lat": spot["lat"],
        "lng": spot["lng"],
        "sources": sources,
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
    success, failed = 0, []

    for spot in SPOTS:
        print(f"[{spot['id']}] {spot['name']} 처리 중...")
        try:
            facts, sources = search_facts(spot["name"])
            story = generate_story(spot["name"], spot["category"], facts)
            save_spot(spot, story, sources)
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
