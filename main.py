from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import spots

app = FastAPI(title="동네도감 API")

# 해커톤용 전체 허용 — 운영 환경에서는 프론트엔드 도메인으로 제한 필요
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(spots.router)


@app.get("/health")
def health():
    return {"status": "ok"}
