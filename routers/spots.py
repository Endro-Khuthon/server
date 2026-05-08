import os
import secrets
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from firebase_client import get_db
from models import StorySpot, StorySpotSummary
from ai.story_service import search_facts, generate_story, discover_spots, fetch_image_url


class GenerateRequest(BaseModel):
    name: str
    category: str
    lat: float
    lng: float


class RegionGenerateRequest(BaseModel):
    region_name: str

router = APIRouter(prefix="/regions", tags=["spots"])


@router.get("", response_model=list[str])
def get_regions():
    db = get_db()
    regions = [doc.id for doc in db.collection("regions").list_documents()]
    return regions


@router.get("/{region_id}/spots", response_model=list[StorySpotSummary])
def get_spots(region_id: str):
    db = get_db()
    docs = db.collection("regions").document(region_id).collection("spots").select(
        ["id", "name", "category", "lat", "lng", "summary"]
    ).stream()
    return [StorySpotSummary(**doc.to_dict()) for doc in docs]


@router.get("/{region_id}/spots/{spot_id}", response_model=StorySpot)
def get_spot(region_id: str, spot_id: str):
    db = get_db()
    doc = db.collection("regions").document(region_id).collection("spots").document(spot_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="스팟을 찾을 수 없습니다")
    return StorySpot(**doc.to_dict())


@router.post("/{region_id}/generate", status_code=201)
def generate_region(region_id: str, req: RegionGenerateRequest, x_api_key: str = Header(...)):
    api_key = os.getenv("API_KEY")
    if not api_key or not secrets.compare_digest(x_api_key, api_key):
        raise HTTPException(status_code=401, detail="인증 실패")
    spots = discover_spots(region_id, req.region_name)
    db = get_db()
    db.collection("regions").document(region_id).set({}, merge=True)
    def process_spot(spot_info):
        facts, sources = search_facts(spot_info.name)
        story = generate_story(spot_info.name, spot_info.category, facts)
        image_url = fetch_image_url(spot_info.name)
        spot = StorySpot(
            id=spot_info.id,
            name=spot_info.name,
            category=spot_info.category,
            lat=spot_info.lat,
            lng=spot_info.lng,
            sources=sources,
            image_url=image_url,
            **story,
        )
        db.collection("regions").document(region_id).collection("spots").document(spot.id).set(spot.model_dump())
        return spot.id

    saved = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_spot, s): s for s in spots}
        for future in as_completed(futures):
            try:
                saved.append(future.result())
            except Exception:
                continue
    return {"region_id": region_id, "saved": saved}


@router.post("/{region_id}/spots/{spot_id}/generate", status_code=201)
def generate_spot(region_id: str, spot_id: str, req: GenerateRequest, x_api_key: str = Header(...)):
    api_key = os.getenv("API_KEY")
    if not api_key or not secrets.compare_digest(x_api_key, api_key):
        raise HTTPException(status_code=401, detail="인증 실패")
    facts, sources = search_facts(req.name)
    story = generate_story(req.name, req.category, facts)
    image_url = fetch_image_url(req.name)
    spot = StorySpot(
        id=spot_id,
        name=req.name,
        category=req.category,
        lat=req.lat,
        lng=req.lng,
        sources=sources,
        image_url=image_url,
        **story,
    )
    db = get_db()
    db.collection("regions").document(region_id).set({}, merge=True)
    db.collection("regions").document(region_id).collection("spots").document(spot_id).set(spot.model_dump())
    return {"id": spot_id}


@router.post("/{region_id}/spots", status_code=201)
def create_spot(region_id: str, spot: StorySpot, x_api_key: str = Header(...)):
    api_key = os.getenv("API_KEY")
    if not api_key or not secrets.compare_digest(x_api_key, api_key):
        raise HTTPException(status_code=401, detail="인증 실패")
    db = get_db()
    db.collection("regions").document(region_id).set({}, merge=True)
    ref = db.collection("regions").document(region_id).collection("spots").document(spot.id)
    ref.set(spot.model_dump())
    return {"id": spot.id}
