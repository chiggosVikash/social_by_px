from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from repositories.base import CRUDBase
from models.core import SocialAccount
from schemas.social_account import SocialAccountCreate
from core.security import encrypt_token

class CRUDSocialAccount(CRUDBase[SocialAccount, SocialAccountCreate]):
    async def create_with_owner(self, db: AsyncSession, *, obj_in: SocialAccountCreate, owner_id: int) -> SocialAccount:
        db_account = SocialAccount(
            platform=obj_in.platform,
            account_id=obj_in.account_id,
            access_token=encrypt_token(obj_in.access_token),
            owner_id=owner_id
        )
        db.add(db_account)
        await db.commit()
        await db.refresh(db_account)
        return db_account

    async def get_by_owner(self, db: AsyncSession, *, id: int, owner_id: int) -> Optional[SocialAccount]:
        stmt = select(SocialAccount).where(
            SocialAccount.id == id,
            SocialAccount.owner_id == owner_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_by_owner(self, db: AsyncSession, *, owner_id: int) -> List[SocialAccount]:
        stmt = select(SocialAccount).where(SocialAccount.owner_id == owner_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

social_account_repo = CRUDSocialAccount(SocialAccount)
