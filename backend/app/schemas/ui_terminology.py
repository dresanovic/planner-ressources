from pydantic import BaseModel


class UiTerminologyResponse(BaseModel):
    labels: dict[str, str]
