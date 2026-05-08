from pydantic import BaseModel


class RelatedContent(BaseModel):
    type: str        # 책/영화/장소
    title: str
    description: str


class StorySpot(BaseModel):
    id: str
    name: str
    category: str    # 역사/건축/인물/전통문화/예술문화/자연문화
    lat: float
    lng: float
    summary: str
    story_past: str
    story_present: str
    story_meaning: str
    keywords: list[str]
    related_contents: list[RelatedContent]
    sources: list[str] = []
    image_url: str = ""


class StorySpotSummary(BaseModel):
    id: str
    name: str
    category: str
    lat: float
    lng: float
    summary: str
