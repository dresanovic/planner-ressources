import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress
from time import monotonic

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
from app.api.schedule_lifecycle import router as schedule_lifecycle_router
from app.api.calendar_workspace import router as calendar_workspace_router
from app.api.lecturer_review import (
    router as lecturer_review_router,
)
from app.api.ui_terminology import router as ui_terminology_router
from app.db.schema import initialize_database
from app.db.session import SessionLocal, engine, get_db
from app.frontend import mount_frontend
from app.services.lecturer_review import (
    cleanup_invalid_source_states,
    is_stored_lecturer_review_secret,
    source_fingerprint_key_from_environment,
)
from app.terminology import load_terminology_from_environment


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _app.state.ui_terminology = load_terminology_from_environment()
    production = os.getenv("APP_ENV", "").casefold() == "production"
    source_fingerprint_key_from_environment(production=production)
    uses_default_database = get_db not in _app.dependency_overrides
    if uses_default_database:
        initialize_database(engine)
    cleanup_task = (
        asyncio.create_task(_cleanup_lecturer_review_source_state())
        if uses_default_database
        else None
    )
    try:
        yield
    finally:
        if cleanup_task is not None:
            cleanup_task.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup_task


async def _cleanup_lecturer_review_source_state() -> None:
    while True:
        cycle_started = monotonic()
        try:
            with SessionLocal() as db:
                cleanup_invalid_source_states(db)
                db.commit()
        except Exception:
            logging.getLogger(__name__).exception(
                "Lecturer review privacy cleanup failed; retrying."
            )
            await asyncio.sleep(5)
            continue
        elapsed = monotonic() - cycle_started
        await asyncio.sleep(max(0.0, 30.0 - elapsed))


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


_LECTURER_PUBLIC_OPERATIONS = {
    ("GET", "/api/public/lecturer-review"),
    ("POST", "/api/public/lecturer-review/feedback"),
    ("GET", "/api/public/ui-terminology"),
}


@app.middleware("http")
async def reject_lecturer_credentials_on_planner_apis(
    request: Request,
    call_next,
):
    operation = (request.method.upper(), request.url.path)
    if (
        request.url.path.startswith("/api/")
        and operation not in _LECTURER_PUBLIC_OPERATIONS
    ):
        authorization = request.headers.get("authorization", "")
        scheme, separator, secret = authorization.partition(" ")
        if separator and scheme.casefold() == "bearer":
            with SessionLocal() as db:
                is_lecturer_secret = is_stored_lecturer_review_secret(
                    db, secret
                )
            if is_lecturer_secret:
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": "PLANNER_AUTHORIZATION_REQUIRED",
                        "message": "Planner authorization is required.",
                    },
                )
    return await call_next(request)


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
app.include_router(schedule_lifecycle_router)
app.include_router(calendar_workspace_router)
app.include_router(lecturer_review_router)
app.include_router(ui_terminology_router)


@app.exception_handler(RequestValidationError)
async def structured_holiday_validation_errors(request: Request, exc: RequestValidationError):
    if not (request.url.path.startswith("/api/holidays") or request.url.path.startswith("/api/exam") or request.url.path.startswith("/api/schedule-revisions") or (request.url.path.startswith("/api/semesters/") and (request.url.path.endswith("/schedule-lifecycle") or request.url.path.endswith("/schedule-revisions"))) or (request.url.path.startswith("/api/courses/") and (request.url.path.endswith("/exam-configuration") or request.url.path.endswith("/exam-sessions")))):
        return await request_validation_exception_handler(request, exc)
    errors = []
    for item in exc.errors():
        location = item.get("loc", ())
        field = str(location[-1]) if location and location[-1] not in {"body", "query", "path"} else None
        structured = {
            "code": "validation_error" if (request.url.path.startswith("/api/schedule-revisions") or request.url.path.startswith("/api/semesters/")) else "VALIDATION_ERROR",
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


mount_frontend(app)
