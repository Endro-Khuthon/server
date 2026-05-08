import os
import secrets
from fastapi import APIRouter, HTTPException, Header
from firebase_client import get_db
from models import StorySpot, StorySpotSummary

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
