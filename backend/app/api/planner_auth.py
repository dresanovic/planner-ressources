from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.planner_auth import (
    AccountAccessRedemptionRequest,
    AccountWithOneTimeAccess,
    AdministratorRecoveryRequest,
    BootstrapRequest,
    CreatePlannerAccountRequest,
    CurrentAccount,
    LoginRequest,
    OneTimeAccess,
    PasswordChangeRequest,
    PlannerAccountList,
    PlannerAccountProjection,
    RevisionRequest,
    SafeError,
    TransferRequest,
)
from app.services.planner_auth import (
    AuthenticatedPlanner,
    PlannerAuthFailure,
    account_projection,
    bootstrap_administrator,
    change_password,
    create_planner_account,
    current_account_projection,
    disable_account,
    end_authenticated_session,
    issue_reactivation_access,
    issue_reset_access,
    list_planner_accounts,
    login_planner,
    recover_administrator,
    redeem_account_access,
    reissue_setup_access,
    transfer_administration,
)


router = APIRouter(tags=["planner authentication"])
NO_STORE = {"Cache-Control": "no-store"}


def planner_cookie_name() -> str:
    return "__Host-planner_session" if os.getenv("APP_ENV", "").casefold() == "production" else "planner_session"


def set_planner_cookie(response: Response, raw_secret: str) -> None:
    production = os.getenv("APP_ENV", "").casefold() == "production"
    response.set_cookie(
        planner_cookie_name(),
        raw_secret,
        secure=production,
        httponly=True,
        samesite="strict",
        path="/",
    )


def clear_planner_cookie(response: Response) -> None:
    response.delete_cookie(
        planner_cookie_name(),
        secure=os.getenv("APP_ENV", "").casefold() == "production",
        httponly=True,
        samesite="strict",
        path="/",
    )


def _auth(request: Request) -> AuthenticatedPlanner:
    return request.state.planner_auth


def _failure(exc: PlannerAuthFailure) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
        headers=NO_STORE,
    )


def _issued_payload(result) -> AccountWithOneTimeAccess:
    return AccountWithOneTimeAccess(
        account=PlannerAccountProjection.model_validate(account_projection(result.account)),
        one_time_access=OneTimeAccess(
            credential=result.raw_secret,
            purpose=result.purpose,
            expires_at=result.expires_at,
        ),
    )


@router.post("/api/auth/bootstrap", status_code=204, responses={400: {"model": SafeError}, 409: {"model": SafeError}})
def bootstrap(payload: BootstrapRequest, db: Session = Depends(get_db)):
    try:
        bootstrap_administrator(
            db,
            startup_credential=payload.startup_credential,
            login_name=payload.login_name,
            display_name=payload.display_name,
            password=payload.password,
        )
        db.commit()
        return Response(status_code=204, headers=NO_STORE)
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)


@router.post("/api/auth/login", response_model=CurrentAccount, responses={401: {"model": SafeError}})
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = login_planner(db, login_name=payload.login_name, password=payload.password)
        db.commit()
        response = JSONResponse(
            content=current_account_projection(result.account),
            headers=NO_STORE,
        )
        set_planner_cookie(response, result.raw_secret)
        return response
    except PlannerAuthFailure as exc:
        if exc.code == "login_failed":
            db.commit()
        else:
            db.rollback()
        return _failure(exc)


@router.post("/api/auth/account-access/redemption", status_code=204, responses={400: {"model": SafeError}, 409: {"model": SafeError}})
def redeem_access(payload: AccountAccessRedemptionRequest, db: Session = Depends(get_db)):
    try:
        redeem_account_access(db, access_credential=payload.access_credential, password=payload.password)
        db.commit()
        return Response(status_code=204, headers=NO_STORE)
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)


@router.post("/api/auth/administrator-recovery", status_code=204, responses={400: {"model": SafeError}, 409: {"model": SafeError}})
def administrator_recovery(payload: AdministratorRecoveryRequest, db: Session = Depends(get_db)):
    try:
        recover_administrator(db, startup_credential=payload.startup_credential, password=payload.password)
        db.commit()
        return Response(status_code=204, headers=NO_STORE)
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)


@router.get("/api/auth/session", response_model=CurrentAccount, responses={401: {"model": SafeError}})
def inspect_session(request: Request):
    return JSONResponse(content=current_account_projection(_auth(request).account), headers=NO_STORE)


@router.post("/api/auth/logout", status_code=204, responses={401: {"model": SafeError}})
def logout(request: Request, db: Session = Depends(get_db)):
    authenticated = _auth(request)
    end_authenticated_session(
        db,
        account_id=authenticated.account.id,
        secret_digest=authenticated.secret_digest,
    )
    db.commit()
    response = Response(status_code=204, headers=NO_STORE)
    clear_planner_cookie(response)
    return response


@router.post("/api/auth/password-change", status_code=204, responses={400: {"model": SafeError}, 401: {"model": SafeError}})
def password_change(payload: PasswordChangeRequest, request: Request, db: Session = Depends(get_db)):
    try:
        change_password(
            db,
            account_id=_auth(request).account.id,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
        db.commit()
        response = Response(status_code=204, headers=NO_STORE)
        clear_planner_cookie(response)
        return response
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)


@router.get("/api/planner-accounts", response_model=PlannerAccountList, responses={403: {"model": SafeError}})
def accounts(request: Request, db: Session = Depends(get_db)):
    try:
        return PlannerAccountList(accounts=list_planner_accounts(db, _auth(request).account.id))
    except PlannerAuthFailure as exc:
        return _failure(exc)


@router.post("/api/planner-accounts", response_model=AccountWithOneTimeAccess, status_code=201)
def create_account(payload: CreatePlannerAccountRequest, request: Request, db: Session = Depends(get_db)):
    try:
        result = create_planner_account(
            db,
            administrator_id=_auth(request).account.id,
            login_name=payload.login_name,
            display_name=payload.display_name,
        )
        db.commit()
        return _issued_payload(result)
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)


@router.post("/api/planner-accounts/{account_id}/setup-access", response_model=AccountWithOneTimeAccess)
def setup_access(account_id: int, payload: RevisionRequest, request: Request, db: Session = Depends(get_db)):
    try:
        result = reissue_setup_access(db, administrator_id=_auth(request).account.id, account_id=account_id, expected_revision=payload.expected_revision)
        db.commit()
        return _issued_payload(result)
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)


@router.post("/api/planner-accounts/{account_id}/reset-access", response_model=AccountWithOneTimeAccess)
def reset_access(account_id: int, payload: RevisionRequest, request: Request, db: Session = Depends(get_db)):
    try:
        result = issue_reset_access(db, administrator_id=_auth(request).account.id, account_id=account_id, expected_revision=payload.expected_revision)
        db.commit()
        return _issued_payload(result)
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)


@router.post("/api/planner-accounts/{account_id}/disable", response_model=PlannerAccountProjection)
def disable(account_id: int, payload: RevisionRequest, request: Request, db: Session = Depends(get_db)):
    try:
        account = disable_account(db, administrator_id=_auth(request).account.id, account_id=account_id, expected_revision=payload.expected_revision)
        db.commit()
        return PlannerAccountProjection.model_validate(account_projection(account))
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)


@router.post("/api/planner-accounts/{account_id}/reactivation-access", response_model=AccountWithOneTimeAccess)
def reactivation_access(account_id: int, payload: RevisionRequest, request: Request, db: Session = Depends(get_db)):
    try:
        result = issue_reactivation_access(db, administrator_id=_auth(request).account.id, account_id=account_id, expected_revision=payload.expected_revision)
        db.commit()
        return _issued_payload(result)
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)


@router.post("/api/planner-accounts/{account_id}/administrator-transfer", response_model=CurrentAccount)
def administrator_transfer(account_id: int, payload: TransferRequest, request: Request, db: Session = Depends(get_db)):
    try:
        former = transfer_administration(
            db,
            administrator_id=_auth(request).account.id,
            target_id=account_id,
            expected_administrator_revision=payload.expected_administrator_revision,
            expected_target_revision=payload.expected_target_revision,
        )
        db.commit()
        return CurrentAccount.model_validate(current_account_projection(former))
    except PlannerAuthFailure as exc:
        db.rollback()
        return _failure(exc)
