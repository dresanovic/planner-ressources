from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse
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
from app.api.conflict_aware_generation import router as conflict_aware_router
from app.api.resource_catalog import academic_router as academic_resource_router, router as resource_catalog_router
from app.api.holiday_calendar import router as holiday_calendar_router
from app.api.exam_scheduling import router as exam_scheduling_router
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
app.include_router(conflict_aware_router)
app.include_router(planning_options_router)
app.include_router(academic_catalog_router)
app.include_router(resource_catalog_router)
app.include_router(academic_resource_router)
app.include_router(holiday_calendar_router)
app.include_router(exam_scheduling_router)


@app.exception_handler(RequestValidationError)
async def structured_holiday_validation_errors(request: Request, exc: RequestValidationError):
    if not (request.url.path.startswith("/api/holidays") or request.url.path.startswith("/api/exam") or (request.url.path.startswith("/api/courses/") and (request.url.path.endswith("/exam-configuration") or request.url.path.endswith("/exam-sessions")))):
        return await request_validation_exception_handler(request, exc)
    errors = []
    for item in exc.errors():
        location = item.get("loc", ())
        field = str(location[-1]) if location and location[-1] not in {"body", "query", "path"} else None
        structured = {
            "code": "VALIDATION_ERROR",
            "message": item.get("msg", "Invalid holiday request."),
            "field": field,
        }
        if request.url.path.startswith("/api/holidays"):
            structured["meta"] = None
        errors.append(structured)
    return JSONResponse(status_code=422, content={"errors": errors})


@app.get("/health")
def health_check():
    return {"status": "ok"}
