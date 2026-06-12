from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.session import get_db
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from repositories.project import project_repo
# [DRY] — Auth dependency imported from shared module
from api.deps import get_current_user_id

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project_in: ProjectCreate, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    return await project_repo.create_with_keywords(db=db, obj_in=project_in, owner_id=current_user_id)

@router.get("", response_model=List[ProjectResponse])
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

@router.post("/{project_id}/workflow", status_code=status.HTTP_202_ACCEPTED)
async def run_project_workflow(project_id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    project = await project_repo.get_with_keywords(db=db, id=project_id, owner_id=current_user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    from workers.queue import enqueue_workflow
    enqueue_workflow(project_id)
    return {"message": "Workflow queued successfully"}

@router.get("/{project_id}/status")
async def get_workflow_status(project_id: int, current_user_id: int = Depends(get_current_user_id)):
    from workers.queue import redis_conn
    status_val = redis_conn.get(f"workflow:project:{project_id}:status")
    
    if status_val:
        if isinstance(status_val, bytes):
            return {"status": status_val.decode('utf-8')}
        return {"status": str(status_val)}
    return {"status": "Not started"}

@router.get("/{project_id}/preview")
async def get_project_preview(project_id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    from repositories.article import article_repo
    # Get all articles for this project
    articles = await article_repo.get_articles_for_project(db, project_id)
    
    # Format them for preview
    preview_data = []
    for article in articles:
        preview_data.append({
            "id": article.id,
            "title": article.title,
            "summary": article.summary,
            "url": article.url,
            "slides": [
                {
                    "id": slide.id,
                    "order_index": slide.order_index,
                    "text_content": slide.text_content,
                    "image_url": slide.image_url
                } for slide in sorted(article.slides, key=lambda s: s.order_index)
            ]
        })
    return {"articles": preview_data}

