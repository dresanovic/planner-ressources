from fastapi import APIRouter, Request, Response

from app.schemas.ui_terminology import UiTerminologyResponse


router = APIRouter()


@router.get(
    "/api/public/ui-terminology",
    response_model=UiTerminologyResponse,
)
def read_ui_terminology(request: Request, response: Response) -> UiTerminologyResponse:
    response.headers["Cache-Control"] = "no-store"
    return UiTerminologyResponse(labels=dict(request.app.state.ui_terminology))
