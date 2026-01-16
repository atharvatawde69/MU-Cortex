from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, subjects, videos

app = FastAPI(title="MU Cortex Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(videos.router)


@app.get("/health")
def health():
    return {"status": "healthy"}

