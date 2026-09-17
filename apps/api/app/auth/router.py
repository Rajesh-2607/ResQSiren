from fastapi import APIRouter, HTTPException, status

from app.auth.deps import ROLES
from app.auth.jwt import create_access_token
from app.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    if body.role not in ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UNKNOWN_ROLE")
    token = create_access_token(username=body.username, role=body.role)
    return LoginResponse(access_token=token)
