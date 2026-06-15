from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
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
    
    from models.core import WorkflowRun
    workflow_run = WorkflowRun(
        project_id=project_id,
        status="Starting workflow..."
    )
    db.add(workflow_run)
    await db.commit()
    await db.refresh(workflow_run)
    
    from workers.queue import enqueue_workflow
    enqueue_workflow(workflow_run.id) # type: ignore
    return {"message": "Workflow queued successfully"}

@router.get("/{project_id}/status")
async def get_workflow_status(project_id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    from models.core import WorkflowRun
    from sqlalchemy import select
    
    result = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.project_id == project_id)
        .order_by(WorkflowRun.started_at.desc())
        .limit(1)
    )
    latest_run = result.scalar_one_or_none()
    
    if latest_run:
        return {"status": latest_run.status}
        
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
                    "hook_type": slide.hook_type,
                    "text_content": slide.text_content,
                    "caption": slide.caption,
                    "image_url": slide.image_url,
                    "emoji": slide.emoji,
                    "text_zone": getattr(slide, "text_zone", None),
                    "visual_type": getattr(slide, "visual_type", None),
                } for slide in sorted(article.slides, key=lambda s: s.order_index)
            ]
        })
    return {"articles": preview_data}


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    project = await project_repo.get_with_keywords(db=db, id=project_id, owner_id=current_user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project_in.name is not None:
        project.name = project_in.name
    if project_in.industry is not None:
        project.industry = project_in.industry
    if project_in.avoid_image_generation is not None:
        project.avoid_image_generation = project_in.avoid_image_generation
    if project_in.background_image_url is not None:
        project.background_image_url = project_in.background_image_url
    if project_in.style_preset is not None:
        project.style_preset = project_in.style_preset
        
    await db.commit()
    await db.refresh(project)
    return project


@router.post("/{project_id}/background", response_model=ProjectResponse)
async def upload_project_background(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    project = await project_repo.get_with_keywords(db=db, id=project_id, owner_id=current_user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    from core.config import get_settings
    settings = get_settings()
    
    # Validate file size (max 5MB)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > settings.MAX_BACKGROUND_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 5MB.")
        
    # Validate format
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, WebP.")
        
    # Read file content
    file_data = await file.read()
    
    # Generate file name and upload
    import uuid
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "webp"
    file_name = f"projects/project_{project_id}_background_{uuid.uuid4().hex[:8]}.{ext}"
    
    from services.storage import upload_file
    bg_url = await upload_file(file_data, file_name, content_type=file.content_type or "image/webp")
    
    project.background_image_url = bg_url
    await db.commit()
    await db.refresh(project)
    
    # Trigger background rendering if avoid_image_generation is True
    if project.avoid_image_generation:
        try:
            from workers.queue import enqueue_project_rerender
            enqueue_project_rerender(project.id)
        except ImportError:
            pass
            
    return project

