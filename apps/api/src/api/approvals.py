from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from api.deps import get_db, get_current_user_id
from repositories.article import article_repo

router = APIRouter(prefix="/approvals", tags=["Approvals"])

class SlideOut(BaseModel):
    id: int
    text_content: str
    image_url: str | None = None
    caption: str | None = None
    emoji: str | None = None
    text_zone: str | None = None
    visual_type: str | None = None

class ApprovalItemOut(BaseModel):
    id: int
    project_id: int
    project_name: str
    article_title: str
    slides: List[SlideOut]
    avoid_image_generation: bool = False
    background_image_url: str | None = None

@router.get("/pending", response_model=List[ApprovalItemOut])
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Get all pending approvals for the current user.
    """
    articles = await article_repo.get_pending_approvals(db, owner_id=user_id)
    
    # Format the data for the frontend
    items = []
    for article in articles:
        slides_out = []
        for slide in sorted(article.slides, key=lambda s: s.order_index):
            if slide.text_content:
                slides_out.append(SlideOut(
                    id=slide.id,
                    text_content=slide.text_content,
                    image_url=slide.image_url,
                    caption=slide.caption,
                    emoji=slide.emoji,
                    text_zone=getattr(slide, "text_zone", None),
                    visual_type=getattr(slide, "visual_type", None),
                ))
        
        items.append(ApprovalItemOut(
            id=article.id,
            project_id=article.project_id, # type: ignore
            project_name=article.project.name if article.project else "Unknown Project",
            article_title=article.title,
            slides=slides_out,
            avoid_image_generation=article.project.avoid_image_generation if article.project else False,
            background_image_url=article.project.background_image_url if article.project else None
        ))
        
    return items

class StatusUpdateResponse(BaseModel):
    message: str
    id: int

async def _update_status(
    article_id: int, 
    user_id: int, 
    new_status: str, 
    db: AsyncSession, 
    success_message: str
) -> StatusUpdateResponse:
    article = await article_repo.update_article_status(
        db, 
        article_id=article_id, 
        owner_id=user_id, 
        status=new_status
    )
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found or you do not have permission"
        )
        
    return StatusUpdateResponse(message=success_message, id=article.id)


@router.post("/{article_id}/approve", response_model=StatusUpdateResponse)
async def approve_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Approve an article and mark it for publishing.
    """
    response = await _update_status(
        article_id, 
        user_id, 
        "approved", 
        db, 
        "Article approved successfully"
    )

    # Ingest the approved content into the RAG vector store for the creator
    from models.core import Article, Project
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.slides), selectinload(Article.project))
        .where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if article and article.project and article.project.owner_id:
        from services.rag import get_rag_service
        rag_service = get_rag_service()
        rag_service.ingest_approved_slides(
            creator_id=article.project.owner_id,
            slides=article.slides,
            article_title=article.title
        )
        
    return response

@router.post("/{article_id}/reject", response_model=StatusUpdateResponse)
async def reject_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Reject an article.
    """
    return await _update_status(
        article_id, 
        user_id, 
        "rejected", 
        db, 
        "Article rejected successfully"
    )

@router.post("/{article_id}/regenerate", response_model=StatusUpdateResponse)
async def regenerate_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Queue an article for regeneration.
    """
    from models.core import Article, Project
    from sqlalchemy.future import select
    result = await db.execute(
        select(Article)
        .join(Project, Article.project_id == Project.id)
        .where(Article.id == article_id, Project.owner_id == user_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found or you do not have permission")
        
    article.status = "regenerating"
    await db.commit()
    
    from workers.queue import enqueue_article_regeneration
    enqueue_article_regeneration(article_id)
    
    return StatusUpdateResponse(message="Regeneration queued successfully", id=article_id)


class SlideUpdate(BaseModel):
    id: int
    text_content: str

class SlideUpdateList(BaseModel):
    slides: List[SlideUpdate]

@router.put("/{article_id}/slides")
async def update_article_slides(
    article_id: int,
    data: SlideUpdateList,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    from models.core import Article, Project, Slide
    from sqlalchemy.future import select
    
    result = await db.execute(
        select(Article)
        .join(Project, Article.project_id == Project.id)
        .where(Article.id == article_id, Project.owner_id == user_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found or you do not have permission")
        
    slide_ids = [s.id for s in data.slides]
    slides_result = await db.execute(
        select(Slide).where(Slide.article_id == article_id, Slide.id.in_(slide_ids))
    )
    slides = slides_result.scalars().all()
    
    slide_map = {s.id: s for s in slides}
    for slide_data in data.slides:
        if slide_data.id in slide_map:
            slide_map[slide_data.id].text_content = slide_data.text_content
            
    await db.commit()
    return {"message": "Slides updated successfully"}


@router.post("/{article_id}/generate-images", response_model=StatusUpdateResponse)
async def generate_images(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    from models.core import Article, Project
    from sqlalchemy.future import select
    result = await db.execute(
        select(Article)
        .join(Project, Article.project_id == Project.id)
        .where(Article.id == article_id, Project.owner_id == user_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found or you do not have permission")
        
    article.status = "generating_images"
    await db.commit()
    
    from workers.queue import enqueue_image_generation
    enqueue_image_generation(article_id)
    
    return StatusUpdateResponse(message="Image generation queued successfully", id=article_id)
