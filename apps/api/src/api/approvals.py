from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from api.deps import get_db, get_current_user_id
from repositories.article import article_repo

router = APIRouter(prefix="/approvals", tags=["Approvals"])

class ApprovalItemOut(BaseModel):
    id: int
    project_name: str
    article_title: str
    slides: List[str]

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
        slides_content = [slide.text_content for slide in article.slides if slide.text_content]
        
        items.append(ApprovalItemOut(
            id=article.id,
            project_name=article.project.name if article.project else "Unknown Project",
            article_title=article.title,
            slides=slides_content
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
    return await _update_status(
        article_id, 
        user_id, 
        "approved", 
        db, 
        "Article approved successfully"
    )

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
