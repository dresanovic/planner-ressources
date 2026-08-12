from fastapi import APIRouter, status

from app.api.draft_schedule import retired_generation_response
from app.schemas.draft_schedule import RetiredGenerationResponse


router = APIRouter(prefix="/api/draft-schedules/batch", tags=["retired teaching generation"])


@router.post(
    "/prepare",
    response_model=RetiredGenerationResponse,
    status_code=status.HTTP_410_GONE,
    deprecated=True,
)
def prepare_multi_course_generation():
    return retired_generation_response()


@router.post(
    "/generate",
    response_model=RetiredGenerationResponse,
    status_code=status.HTTP_410_GONE,
    deprecated=True,
)
def generate_multi_course_drafts():
    return retired_generation_response()
