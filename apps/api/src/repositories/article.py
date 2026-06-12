from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.core import Article, Slide, Project
from sqlalchemy.orm import selectinload

class ArticleRepository:
    async def save_workflow_results(self, db: AsyncSession, project_id: int, final_state: Dict[str, Any]) -> None:
        """
        Persists approved articles and generated slides from the LangGraph workflow state
        to the database.
        """
        for art_data in final_state.get("approved_articles", []):
            result = await db.execute(select(Article).where(Article.url == art_data["url"]))
            existing_article = result.scalar_one_or_none()
            
            if not existing_article:
                article = Article(
                    project_id=project_id,
                    title=art_data.get("title", "Untitled"),
                    url=art_data.get("url", ""),
                    source=art_data.get("source", "Unknown"),
                    summary=art_data.get("summary", ""),
                    status="pending"
                )
                db.add(article)
                await db.flush() # Get article.id
                
                slides_data = final_state.get("approved_slides", {}).get(article.url, [])
                for i, slide_data in enumerate(slides_data):
                    slide = Slide(
                        article_id=article.id,
                        order_index=i,
                        hook_type=slide_data.get("hook_type", ""),
                        text_content=slide_data.get("text_content", ""),
                        caption=slide_data.get("caption", ""),
                        emoji=slide_data.get("emoji", "")
                    )
                    db.add(slide)
        
        await db.commit()
        
    async def get_articles_for_project(self, db: AsyncSession, project_id: int):
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Article)
            .where(Article.project_id == project_id)
            .options(selectinload(Article.slides))
        )
        return result.scalars().all()

    async def get_pending_approvals(self, db: AsyncSession, owner_id: int):
        """Fetch all pending articles with their slides and project for the given user."""
        result = await db.execute(
            select(Article)
            .join(Project, Article.project_id == Project.id)
            .where(
                Article.status == "pending",
                Project.owner_id == owner_id
            )
            .options(
                selectinload(Article.slides),
                selectinload(Article.project)
            )
            .order_by(Article.published_date.desc().nulls_last(), Article.id.desc())
        )
        return result.scalars().all()

    async def update_article_status(self, db: AsyncSession, article_id: int, owner_id: int, status: str) -> Article | None:
        """Update an article's status, ensuring it belongs to the current user."""
        result = await db.execute(
            select(Article)
            .join(Project, Article.project_id == Project.id)
            .where(
                Article.id == article_id,
                Project.owner_id == owner_id
            )
        )
        article = result.scalar_one_or_none()
        
        if article:
            article.status = status
            await db.commit()
            await db.refresh(article)
            return article
        return None

article_repo = ArticleRepository()
