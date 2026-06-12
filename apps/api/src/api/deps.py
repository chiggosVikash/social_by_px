"""Shared FastAPI dependencies for authentication.

# [SOLID: SRP] — Extracted from projects.py; auth logic has its own home.
# [DRY] — Single source imported by all route modules.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.firebase import verify_firebase_token
from db.session import get_db

security = HTTPBearer()


async def get_current_user_id(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """Extract the current user ID from a Firebase Bearer token.

    Verifies the token, looks up the user by firebase_uid, and auto-creates
    the user record on first sign-in.
    """
    from models.core import User
    from sqlalchemy.future import select

    try:
        decoded_token = verify_firebase_token(credentials.credentials)
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            firebase_uid=firebase_uid,
            email=email or f"{firebase_uid}@example.com",
            hashed_password=None,  # Managed by Firebase
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return int(user.id)  # type: ignore
