from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.draft_schedule import (
    constraints_router,
    overview_router,
    router as draft_schedule_router,
    session_router,
)
from app.api.planning_options import router as planning_options_router
from app.api.academic_catalog import router as academic_catalog_router
from app.api.multi_course_generation import router as multi_course_router
from app.db.schema import initialize_database
from app.db.session import engine, get_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if get_db not in _app.dependency_overrides:
        initialize_database(engine)
    yield


app = FastAPI(title="Planner Resource API", lifespan=lifespan)
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
app.include_router(multi_course_router)
app.include_router(planning_options_router)
app.include_router(academic_catalog_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
