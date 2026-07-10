from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.draft_schedule import (
    constraints_router,
    overview_router,
    router as draft_schedule_router,
    session_router,
)
from app.api.planning_options import router as planning_options_router

app = FastAPI(title="Planner Resource API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(draft_schedule_router)
app.include_router(constraints_router)
app.include_router(overview_router)
app.include_router(session_router)
app.include_router(planning_options_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
