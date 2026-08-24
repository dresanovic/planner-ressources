from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


def _camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class PlannerAuthModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_camel,
        populate_by_name=True,
        extra="forbid",
    )


class BootstrapRequest(PlannerAuthModel):
    startup_credential: str = Field(min_length=64, max_length=64)
    login_name: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(PlannerAuthModel):
    login_name: str = Field(max_length=128)
    password: str = Field(max_length=128)


class AccountAccessRedemptionRequest(PlannerAuthModel):
    access_credential: str = Field(min_length=43, max_length=43)
    password: str = Field(min_length=12, max_length=128)


class AdministratorRecoveryRequest(PlannerAuthModel):
    startup_credential: str = Field(min_length=64, max_length=64)
    password: str = Field(min_length=12, max_length=128)


class PasswordChangeRequest(PlannerAuthModel):
    current_password: str = Field(min_length=12, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class CreatePlannerAccountRequest(PlannerAuthModel):
    login_name: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=200)


class RevisionRequest(PlannerAuthModel):
    expected_revision: int = Field(ge=1)


class TransferRequest(PlannerAuthModel):
    expected_target_revision: int = Field(ge=1)
    expected_administrator_revision: int = Field(ge=1)


class CurrentAccount(PlannerAuthModel):
    id: int = Field(ge=1)
    login_name: str
    display_name: str
    is_administrator: bool


class PlannerAccountProjection(PlannerAuthModel):
    id: int = Field(ge=1)
    login_name: str
    display_name: str
    access_level: str
    state: str
    revision: int = Field(ge=1)
    created_at: datetime
    disabled_at: datetime | None = None
    reactivated_at: datetime | None = None


class PlannerAccountList(PlannerAuthModel):
    accounts: list[PlannerAccountProjection]


class OneTimeAccess(PlannerAuthModel):
    credential: str = Field(min_length=43, max_length=43)
    purpose: str
    expires_at: datetime


class AccountWithOneTimeAccess(PlannerAuthModel):
    account: PlannerAccountProjection
    one_time_access: OneTimeAccess


class SafeError(PlannerAuthModel):
    code: str
    message: str
