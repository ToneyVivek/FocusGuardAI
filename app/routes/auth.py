from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.dependencies.deps import get_current_user, get_db
from app.middleware.rate_limit import limiter
from app.models.models import User
from app.schemas.schemas import (
    AdminRegisterRequest,
    LogoutRequest,
    OnboardingSetup,
    RefreshTokenRequest,
    Token,
    TokenWithRefresh,
    UserResponse,
)
from app.services.auth import authenticate_user, register_bootstrap_admin
from app.services.invitation import process_onboarding_setup
from app.services.refresh_token_service import refresh_token_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def register(request: Request, user_in: AdminRegisterRequest, db: Session = Depends(get_db)):
    """
    Bootstrap registration for the first platform administrator only.
    Employee accounts must onboard via invitation (POST /auth/complete-setup).
    """
    return register_bootstrap_admin(
        db=db,
        email=user_in.email,
        full_name=user_in.full_name,
        password=user_in.password,
    )


@router.post("/login", response_model=TokenWithRefresh)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2-compatible login returning JWT access token and refresh token.
    
    Returns both access token (short-lived) and refresh token (long-lived, 7 days).
    Use refresh token to obtain new access tokens without re-authentication.
    """
    print(f"[AUTH] Login attempt - email: {form_data.username}")
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        print(f"[AUTH] Login failed - user not found or invalid password for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"[AUTH] User authenticated - user_id: {user.id}, email: {user.email}")
    access_token = create_access_token(
        subject=user.email,
        role=user.role,
        user_id=user.id,
    )
    print(f"[AUTH] Access token created - token_length: {len(access_token)}")
    
    # Create refresh token
    refresh_token = refresh_token_service.create_refresh_token(db, user)
    print(f"[AUTH] Refresh token created")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Retrieves the profile of the currently authenticated user."""
    return current_user


@router.post("/complete-setup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def complete_setup(request: Request, setup_in: OnboardingSetup, db: Session = Depends(get_db)):
    """Completes onboarding for an invited employee using a secure invitation token."""
    return process_onboarding_setup(db=db, setup_in=setup_in)


@router.post("/refresh", response_model=TokenWithRefresh)
@limiter.limit("20/minute")
def refresh(request: Request, refresh_in: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    Implements token rotation: old refresh token is invalidated and a new one is issued.
    Returns both new access token and new refresh token.
    """
    try:
        # Rotate refresh token (verifies old token, issues new one)
        new_refresh_token, db_token = refresh_token_service.rotate_refresh_token(
            db=db,
            old_raw_token=refresh_in.refresh_token,
        )
        
        # Create new access token
        user = db_token.user
        access_token = create_access_token(
            subject=user.email,
            role=user.role,
            user_id=user.id,
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        # Log unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token",
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
def logout(
    request: Request,
    logout_in: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logout by revoking the refresh token.
    
    If refresh_token is provided, revokes that specific token.
    If not provided, revokes all refresh tokens for the authenticated user.
    """
    if logout_in.refresh_token:
        # Revoke specific token
        try:
            refresh_token_service.revoke_refresh_token(db, logout_in.refresh_token)
        except HTTPException:
            # If token is invalid, still return success (idempotent logout)
            pass
    else:
        # Revoke all tokens for the user
        refresh_token_service.revoke_all_user_tokens(db, current_user)
    
    return None
