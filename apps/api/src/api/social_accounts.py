from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.session import get_db
from schemas.social_account import SocialAccountCreate, SocialAccountUpdate, SocialAccountResponse
from api.deps import get_current_user_id  # [DRY] — shared auth dependency
from repositories.social_account import social_account_repo

router = APIRouter(prefix="/social-accounts", tags=["social-accounts"])

@router.post("", response_model=SocialAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_social_account(account_in: SocialAccountCreate, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    return await social_account_repo.create_with_owner(db=db, obj_in=account_in, owner_id=current_user_id)

@router.get("", response_model=List[SocialAccountResponse])
async def list_social_accounts(db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    return await social_account_repo.get_multi_by_owner(db=db, owner_id=current_user_id)

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_social_account(account_id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    account = await social_account_repo.get_by_owner(db=db, id=account_id, owner_id=current_user_id)
    if not account:
        raise HTTPException(status_code=404, detail="Social Account not found")
    
    await social_account_repo.remove(db=db, id=account.id)
    return None
