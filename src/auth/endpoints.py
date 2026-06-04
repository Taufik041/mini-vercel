from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col
from schemas import User, Token, SignUpReq
from security import verify, hash
from common.utils import create_access_token, verify_access_token
from datetime import timedelta
import os

ACCESS_TOKEN_EXPIRE_MINUTES: float = float(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 0)
)
router = APIRouter(tags=["auth"], prefix="/auth")


@router.get("/", status_code=status.HTTP_200_OK)
async def home():
    return {"status": "ok"}


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)
):
    existing_user = (
        (await db.execute(select(User).where(col(User.email) == data.username)))
        .scalars()
        .first()
    )
    print(existing_user)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not verify(data.password, existing_user.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="incorrect password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": str(existing_user.id)}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(user=Depends(verify_access_token)):
    return {"message": "Successfully logged out"}


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: SignUpReq, db: AsyncSession = Depends(get_session)):
    existing_user = (
        (await db.execute(select(User).where(col(User.email) == user_data.email)))
        .scalars()
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="passwords don't match"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        creds=user_data.creds,
        password=hash(user_data.password),
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": str(new_user.id)}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
