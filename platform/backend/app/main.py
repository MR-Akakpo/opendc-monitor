from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.global_view import router as global_view_router
from app.api.changeover import router as changeover_router
from app.api.changeover_control import router as changeover_control_router

app = FastAPI(title="OpenDC Monitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(global_view_router)
app.include_router(changeover_router)
app.include_router(changeover_control_router)

@app.get("/")
def root():
    return {"message": "OpenDC Monitor API Running"}

