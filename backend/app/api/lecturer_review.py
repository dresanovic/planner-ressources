from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.lecturer_review import (
    FeedbackInput,
    FeedbackResult,
    IssueLinkInput,
    IssuedLinkResult,
    PlannerError,
    PlannerReviewOverview,
    PublicRefreshRequiredError,
    PublicReview,
    PublicThrottledError,
    PublicUnavailableError,
    PublicValidationError,
    ReplaceLinkInput,
)
from app.services.lecturer_review import (
    LecturerReviewFailure,
    get_lecturer_review_overview,
    get_public_lecturer_review,
    issue_lecturer_review_link,
    replace_lecturer_review_link,
    reject_invalid_feedback_attempt,
    revoke_lecturer_review_link,
    source_fingerprint_key_from_environment,
    submit_lecturer_review_feedback,
)


router = APIRouter(tags=["lecturer review"])
PUBLIC_RESPONSE_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Robots-Tag": "noindex, nofollow",
}


@router.get(
    "/api/schedule-revisions/{revision_id}/lecturer-review",
    response_model=PlannerReviewOverview,
    responses={404: {"model": PlannerError}},
)
def read_lecturer_review_overview(
    revision_id: int,
    db: Session = Depends(get_db),
):
    try:
        result = get_lecturer_review_overview(db, revision_id)
        db.commit()
        return result
    except LecturerReviewFailure as exc:
        db.rollback()
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )


async def _parse_feedback_payload(request: Request) -> FeedbackInput | None:
    try:
        return FeedbackInput.model_validate(await request.json())
    except ValueError:
        return None


@router.post(
    "/api/schedule-revisions/{revision_id}/lecturer-review-links",
    response_model=IssuedLinkResult,
    status_code=201,
    responses={
        404: {"model": PlannerError},
        409: {"model": PlannerError},
        422: {"model": PlannerError},
    },
)
def issue_lecturer_review(
    revision_id: int,
    payload: IssueLinkInput,
    db: Session = Depends(get_db),
):
    try:
        result = issue_lecturer_review_link(
            db,
            revision_id,
            payload.lecturer_id,
            duration_days=payload.duration_days,
        )
        db.commit()
        return result
    except LecturerReviewFailure as exc:
        db.rollback()
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )


@router.post(
    "/api/lecturer-review-links/{link_id}/revoke",
    response_model=PlannerReviewOverview,
    responses={
        404: {"model": PlannerError},
        409: {"model": PlannerError},
    },
)
def revoke_lecturer_review(
    link_id: int,
    db: Session = Depends(get_db),
):
    try:
        result = revoke_lecturer_review_link(db, link_id)
        db.commit()
        return result
    except LecturerReviewFailure as exc:
        db.rollback()
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )


@router.post(
    "/api/lecturer-review-links/{link_id}/replace",
    response_model=IssuedLinkResult,
    status_code=201,
    responses={
        404: {"model": PlannerError},
        409: {"model": PlannerError},
        422: {"model": PlannerError},
    },
)
def replace_lecturer_review(
    link_id: int,
    payload: ReplaceLinkInput,
    db: Session = Depends(get_db),
):
    try:
        result = replace_lecturer_review_link(
            db,
            link_id,
            duration_days=payload.duration_days,
        )
        db.commit()
        return result
    except LecturerReviewFailure as exc:
        db.rollback()
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )


@router.get(
    "/api/public/lecturer-review",
    response_model=PublicReview,
    responses={
        404: {"model": PublicUnavailableError},
        429: {"model": PublicThrottledError},
    },
)
def read_public_lecturer_review(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    secret = _bearer_secret(authorization)
    try:
        result = get_public_lecturer_review(
            db,
            secret,
            source_host=request.client.host if request.client is not None else "",
            source_key=source_fingerprint_key_from_environment(production=False),
        )
        db.commit()
        return JSONResponse(
            status_code=200,
            content=result.model_dump(mode="json", by_alias=True),
            headers=PUBLIC_RESPONSE_HEADERS,
        )
    except LecturerReviewFailure as exc:
        db.commit()
        headers = dict(PUBLIC_RESPONSE_HEADERS)
        if exc.retry_after is not None:
            headers["Retry-After"] = str(exc.retry_after)
        if exc.status_code == 429:
            content = {
                "code": "REVIEW_TEMPORARILY_UNAVAILABLE",
                "message": "This review is temporarily unavailable. Try again later.",
            }
        else:
            content = {
                "code": "REVIEW_UNAVAILABLE",
                "message": (
                    "This review is unavailable. Contact the planner for a new link."
                ),
            }
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )


@router.post(
    "/api/public/lecturer-review/feedback",
    response_model=FeedbackResult,
    status_code=201,
    responses={
        200: {"model": FeedbackResult},
        404: {"model": PublicUnavailableError},
        409: {"model": PublicRefreshRequiredError},
        422: {"model": PublicValidationError},
        429: {"model": PublicThrottledError},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["clientSubmissionId", "kind"],
                        "properties": {
                            "clientSubmissionId": {
                                "type": "string",
                                "format": "uuid",
                            },
                            "kind": {
                                "type": "string",
                                "enum": [
                                    "revision_comment",
                                    "session_comment",
                                    "impossible_session",
                                ],
                            },
                            "sessionRef": {
                                "type": ["string", "null"],
                                "pattern": "^(teaching|exam):[1-9][0-9]*$",
                            },
                            "comment": {
                                "type": ["string", "null"],
                                "description": (
                                    "At most 2000 characters after surrounding "
                                    "whitespace is removed."
                                ),
                            },
                        },
                    }
                }
            },
        }
    },
)
def submit_public_lecturer_feedback(
    request: Request,
    payload: FeedbackInput | None = Depends(_parse_feedback_payload),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    secret = _bearer_secret(authorization)
    source_host = request.client.host if request.client is not None else ""
    source_key = source_fingerprint_key_from_environment(production=False)
    try:
        if payload is None:
            reject_invalid_feedback_attempt(
                db,
                secret,
                source_host=source_host,
                source_key=source_key,
            )
            raise AssertionError("Invalid feedback rejection must raise.")
        result = submit_lecturer_review_feedback(
            db,
            secret,
            payload,
            source_host=source_host,
            source_key=source_key,
        )
        db.commit()
        status_code = 201 if result.outcome == "created" else 200
        return JSONResponse(
            status_code=status_code,
            content=result.model_dump(mode="json", by_alias=True),
            headers=PUBLIC_RESPONSE_HEADERS,
        )
    except LecturerReviewFailure as exc:
        db.commit()
        headers = dict(PUBLIC_RESPONSE_HEADERS)
        if exc.retry_after is not None:
            headers["Retry-After"] = str(exc.retry_after)
        if exc.status_code == 409:
            content = {
                "code": "REVIEW_REFRESH_REQUIRED",
                "message": (
                    "The schedule changed. Reload the browser page or reopen the link before submitting feedback."
                ),
            }
        elif exc.status_code == 422:
            content = {
                "code": "INVALID_FEEDBACK",
                "message": "Feedback must match the current review session.",
            }
        elif exc.status_code == 429:
            content = {
                "code": "REVIEW_TEMPORARILY_UNAVAILABLE",
                "message": "This review is temporarily unavailable. Try again later.",
            }
        else:
            content = {
                "code": "REVIEW_UNAVAILABLE",
                "message": (
                    "This review is unavailable. Contact the planner for a new link."
                ),
            }
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )


def _bearer_secret(authorization: str | None) -> str:
    if authorization is None:
        return ""
    scheme, separator, value = authorization.partition(" ")
    if not separator or scheme.casefold() != "bearer":
        return ""
    return value
