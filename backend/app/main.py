import asyncio
import logging
import os
from contextlib import asynccontextmanager, contextmanager, suppress
from time import monotonic

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse, RedirectResponse
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
from app.api.planner_auth import (
    clear_planner_cookie,
    planner_cookie_name,
    router as planner_auth_router,
)
from app.db.schema import initialize_database
from app.db.session import SessionLocal, engine, get_db
from app.frontend import (
    development_cors_origins,
    is_public_unauthenticated_browser_path,
    mount_frontend,
)
from app.services.lecturer_review import (
    cleanup_invalid_source_states,
    institution_timezone_from_environment,
    is_stored_lecturer_review_secret,
    source_fingerprint_key_from_environment,
)
from app.services.planner_auth import (
    PlannerAuthFailure,
    SESSION_ENDED_MESSAGE,
    authenticate_session,
    reconcile_startup_credentials,
    touch_session_if_current,
)
from app.terminology import load_terminology_from_environment


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _app.state.ui_terminology = load_terminology_from_environment()
    production = os.getenv("APP_ENV", "").casefold() == "production"
    source_fingerprint_key_from_environment(production=production)
    institution_timezone_from_environment()
    uses_default_database = get_db not in _app.dependency_overrides
    if uses_default_database:
        initialize_database(engine)
        with SessionLocal() as db:
            reconcile_startup_credentials(
                db,
                bootstrap_credential=os.getenv("PLANNER_BOOTSTRAP_CREDENTIAL") or None,
                recovery_credential=os.getenv("PLANNER_ADMIN_RECOVERY_CREDENTIAL") or None,
            )
            db.commit()
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


_PUBLIC_API_OPERATIONS = {
    ("GET", "/health"),
    ("GET", "/api/public/lecturer-review"),
    ("GET", "/api/public/lecturer-review/calendar"),
    ("POST", "/api/public/lecturer-review/feedback"),
    ("GET", "/api/public/ui-terminology"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/bootstrap"),
    ("POST", "/api/auth/account-access/redemption"),
    ("POST", "/api/auth/administrator-recovery"),
}
_PUBLIC_UNSAFE_AUTH_OPERATIONS = {
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/bootstrap"),
    ("POST", "/api/auth/account-access/redemption"),
    ("POST", "/api/auth/administrator-recovery"),
}
@contextmanager
def _authorization_session():
    """Use the request database, including ordinary FastAPI test overrides."""
    override = app.dependency_overrides.get(get_db)
    if override is None:
        with SessionLocal() as db:
            yield db
        return
    supplied = override()
    if hasattr(supplied, "__next__"):
        try:
            yield next(supplied)
        finally:
            supplied.close()
    else:
        yield supplied


@app.middleware("http")
async def enforce_planner_authorization(
    request: Request,
    call_next,
):
    operation = (request.method.upper(), request.url.path)
    unsafe = request.method.upper() not in {"GET", "HEAD", "OPTIONS"}
    public_api = operation in _PUBLIC_API_OPERATIONS
    protected_api = request.url.path.startswith("/api/") and not public_api
    protected_docs = request.url.path in {"/docs", "/redoc", "/openapi.json"}
    public_browser = is_public_unauthenticated_browser_path(request.url.path)
    backend_path = request.url.path.startswith("/api/") or request.url.path in {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    protected_browser = not backend_path and not public_browser

    needs_csrf = unsafe and (protected_api or operation in _PUBLIC_UNSAFE_AUTH_OPERATIONS)
    if needs_csrf and request.headers.get("x-csrf-protection") != "1":
        return JSONResponse(
            status_code=403,
            content={"code": "csrf_protection_required", "message": "Die Anfrage konnte nicht bestätigt werden."},
            headers={"Cache-Control": "no-store"},
        )
    needs_json = needs_csrf and operation != ("POST", "/api/auth/logout")
    if needs_json and request.headers.get("content-type", "").partition(";")[0].strip().casefold() != "application/json":
        return JSONResponse(
            status_code=415,
            content={"code": "json_required", "message": "Die Anfrage muss als JSON gesendet werden."},
            headers={"Cache-Control": "no-store"},
        )

    if protected_api or protected_docs or protected_browser:
        authorization = request.headers.get("authorization", "")
        scheme, separator, secret = authorization.partition(" ")
        if separator and scheme.casefold() == "bearer":
            with _authorization_session() as db:
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
                    headers={"Cache-Control": "no-store"},
                )
        raw_session = request.cookies.get(planner_cookie_name())
        try:
            with _authorization_session() as db:
                try:
                    authenticated = authenticate_session(db, raw_session)
                except PlannerAuthFailure:
                    db.commit()
                    raise
                db.expunge(authenticated.account)
                db.expunge(authenticated.session)
            request.state.planner_auth = authenticated
        except PlannerAuthFailure:
            if protected_browser:
                response = RedirectResponse("/login/", status_code=307, headers={"Cache-Control": "no-store"})
            else:
                response = JSONResponse(
                    status_code=401,
                    content={"code": "session_ended", "message": SESSION_ENDED_MESSAGE},
                    headers={"Cache-Control": "no-store"},
                )
            clear_planner_cookie(response)
            return response

        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        if response.status_code < 400 and request.headers.get("x-planner-activity") == "user":
            with _authorization_session() as db:
                touch_session_if_current(
                    db,
                    account_id=authenticated.account.id,
                    secret_digest=authenticated.secret_digest,
                )
                db.commit()
        return response
    return await call_next(request)


# Register CORS after the authorization middleware so it remains the outer
# layer and can answer browser preflights before planner authentication runs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=development_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "X-CSRF-Protection",
        "X-Planner-Activity",
    ],
    expose_headers=["Content-Disposition"],
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
app.include_router(schedule_lifecycle_router)
app.include_router(calendar_workspace_router)
app.include_router(lecturer_review_router)
app.include_router(ui_terminology_router)
app.include_router(planner_auth_router)


@app.exception_handler(RequestValidationError)
async def structured_holiday_validation_errors(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api/auth/") or request.url.path.startswith("/api/planner-accounts"):
        return JSONResponse(
            status_code=400,
            content={"code": "invalid_request", "message": "Prüfen Sie Ihre Angaben und versuchen Sie es erneut."},
            headers={"Cache-Control": "no-store"},
        )
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
