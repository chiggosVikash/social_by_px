from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.session import get_db
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from repositories.project import project_repo

router = APIRouter(prefix="/projects", tags=["projects"])

# Mocking authentication for now
async def get_current_user_id() -> int:
    return 1 # We will implement real auth later

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project_in: ProjectCreate, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    return await project_repo.create_with_keywords(db=db, obj_in=project_in, owner_id=current_user_id)

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    return await project_repo.get_multi_by_owner(db=db, owner_id=current_user_id)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    project = await project_repo.get_with_keywords(db=db, id=project_id, owner_id=current_user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    project = await project_repo.get_with_keywords(db=db, id=project_id, owner_id=current_user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await project_repo.remove(db=db, id=project.id)
    return None
