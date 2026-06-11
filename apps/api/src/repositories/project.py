from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from repositories.base import CRUDBase
from models.core import Project, ProjectKeyword
from schemas.project import ProjectCreate

class CRUDProject(CRUDBase[Project, ProjectCreate]):
    async def create_with_keywords(self, db: AsyncSession, *, obj_in: ProjectCreate, owner_id: int) -> Project:
        db_project = Project(
            name=obj_in.name,
            industry=obj_in.industry,
            owner_id=owner_id
        )
        db.add(db_project)
        await db.flush()
        
        for kw in obj_in.keywords:
            db_kw = ProjectKeyword(project_id=db_project.id, keyword=kw)
            db.add(db_kw)
            
        await db.commit()
        return await self.get_with_keywords(db, id=db_project.id, owner_id=owner_id)

    async def get_with_keywords(self, db: AsyncSession, *, id: int, owner_id: int) -> Optional[Project]:
        stmt = select(Project).options(selectinload(Project.keywords)).where(
            Project.id == id,
            Project.owner_id == owner_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_by_owner(self, db: AsyncSession, *, owner_id: int) -> List[Project]:
        stmt = select(Project).options(selectinload(Project.keywords)).where(
            Project.owner_id == owner_id
        )
        result = await db.execute(stmt)
        return result.scalars().all()

project_repo = CRUDProject(Project)
