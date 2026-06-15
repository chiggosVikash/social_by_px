import asyncio
import logging
import json
import uuid
from typing import Optional, AsyncGenerator, Tuple, Any, cast
from contextlib import asynccontextmanager

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.config import get_settings
from db import session as db_session
from models.core import Article, Project, Slide, WorkflowRun
from repositories.project import project_repo
from repositories.article import article_repo
from agents.graph import app_graph
from agents.state import GraphState
from agents.nodes import content_generation_agent, slide_verification_agent
from services.storage import upload_file
from services.image import SlideImageStrategyFactory

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Core Utilities & Services
# -----------------------------------------------------------------------------

PROGRESS_RULES = {
    "Not started": 0,
    "Completed": 100
}

def get_progress_value(status: str) -> int:
    if status in PROGRESS_RULES:
        return PROGRESS_RULES[status]
    
    status_lower = status.lower()
    if "starting" in status_lower: return 5
    if "verify_slides" in status_lower: return 80
    if "verify" in status_lower: return 40
    if "research" in status_lower: return 20
    if "refine" in status_lower: return 45
    if "generate" in status_lower: return 60
    if "publish" in status_lower: return 95
    return 10


class ProgressNotifier:
    """Encapsulates Redis publishing logic for progress updates."""
    def __init__(self, redis_client: redis.Redis, project_id: int):
        self.redis_client = redis_client
        self.project_id = project_id
        self.topic = f"workflow:progress:{project_id}"

    async def publish(self, status: str, is_failed: bool = False) -> None:
        progress = get_progress_value(status)
        payload = {
            "status": status,
            "progress": progress,
            "is_failed": is_failed
        }
        await self.redis_client.publish(self.topic, json.dumps(payload))


@asynccontextmanager
async def worker_context(project_id: Optional[int] = None) -> AsyncGenerator[Tuple[Any, redis.Redis, Optional[ProgressNotifier]], None]:
    """
    Context manager that sets up the database session and Redis client for worker tasks.
    It guarantees teardown and yields a ProgressNotifier if project_id is provided.
    """
    settings = get_settings()
    redis_client = redis.from_url(settings.REDIS_URL)
    maker = db_session.async_session_maker or db_session.init_db()
    
    notifier = ProgressNotifier(redis_client, project_id) if project_id else None

    try:
        async with maker() as db:
            yield db, redis_client, notifier
    finally:
        await redis_client.aclose()


# -----------------------------------------------------------------------------
# Worker Tasks
# -----------------------------------------------------------------------------

def run_workflow_task(run_id: int):
    """
    Runs the LangGraph workflow for a given project synchronously (for RQ workers).
    """
    asyncio.run(_run_workflow_async(run_id))

async def _run_workflow_async(run_id: int):
    # Setup initially without project_id, fetch it, then we could use notifier.
    # We'll just instantiate ProgressNotifier manually once we have project_id inside the DB context.
    async with worker_context() as (db, redis_client, _):
        result = await db.execute(
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.project))
            .where(WorkflowRun.id == run_id)
        )
        workflow_run = result.scalar_one_or_none()
        
        if not workflow_run or not workflow_run.project_id:
            logger.error(f"WorkflowRun {run_id} not found or missing project_id.")
            return

        project_id = cast(int, workflow_run.project_id)
        owner_id = cast(int, workflow_run.project.owner_id) if workflow_run.project else 0
        notifier = ProgressNotifier(redis_client, project_id)

        try:
            # Fetch project with keywords
            project = await project_repo.get_with_keywords(db, id=project_id, owner_id=owner_id)
            if not project:
                workflow_run.status = "Failed"
                workflow_run.error_message = f"Project {project_id} not found."
                await db.commit()
                await notifier.publish("Failed", is_failed=True)
                return

            keywords = [kw.keyword for kw in project.keywords]
            
            initial_state: GraphState = {
                "project_id": project_id,
                "creator_id": owner_id,
                "keywords": keywords,
                "industry": str(project.industry or ""),
                "rag_context": None,
                "search_queries": [],
                "current_articles": [],
                "retries": 0,
                "approved_articles": [],
                "generated_slides": {},
                "approved_slides": {},
                "publish_status": ""
            }
            
            workflow_run.status = "Starting workflow..."
            await db.commit()
            await notifier.publish("Starting workflow...")
            
            final_state = None
            async for event in app_graph.astream(initial_state, stream_mode="values"):
                final_state = event
                
                # Deduce progress from state presence
                status_parts = []
                if event.get("current_articles"): status_parts.append("research")
                if event.get("approved_articles"): status_parts.append("verify")
                if event.get("generated_slides"): status_parts.append("generate")
                if event.get("approved_slides"): status_parts.append("verify_slides")
                if event.get("publish_status"): status_parts.append("publish")
                
                latest_node = status_parts[-1] if status_parts else "starting"
                status_msg = f"Agent '{latest_node}' is working..."
                
                workflow_run.status = status_msg
                await db.commit()
                await notifier.publish(status_msg)

            if not final_state:
                raise RuntimeError("Workflow produced no output")

            logger.info(f"Workflow completed for project {project_id}.")
            
            await article_repo.save_workflow_results(db, project_id, final_state)
            logger.info(f"Persisted articles and slides to database for project {project_id}.")
            
            # [SOLID: SRP] Auto-render slide templates if user chose to avoid AI image generation
            if project.avoid_image_generation and project.background_image_url:
                result = await db.execute(
                    select(Article)
                    .options(selectinload(Article.slides))
                    .where(Article.project_id == project_id, Article.status == "pending")
                )
                pending_articles = result.scalars().all()
                for article in pending_articles:
                    if any(s.image_url is None for s in article.slides):
                        await _render_slides_for_article(db, article, project)
            
            workflow_run.status = "Completed"
            await db.commit()
            await notifier.publish("Completed")
            
        except Exception as e:
            logger.exception(f"Workflow {run_id} failed with error: {e}")
            if workflow_run:
                workflow_run.status = "Failed"
                workflow_run.error_message = str(e)
                await db.commit()
            await notifier.publish("Failed", is_failed=True)


def run_article_regeneration_task(article_id: int):
    asyncio.run(_run_article_regeneration_async(article_id))

async def _run_article_regeneration_async(article_id: int):
    async with worker_context() as (db, redis_client, _):
        result = await db.execute(
            select(Article)
            .options(
                selectinload(Article.project).selectinload(Project.keywords),
                selectinload(Article.slides)
            )
            .where(Article.id == article_id)
        )
        article = result.scalar_one_or_none()
        
        if not article or not article.project_id:
            logger.error(f"Article {article_id} not found or missing project_id.")
            return

        project_id = cast(int, article.project_id)
        project = article.project
        notifier = ProgressNotifier(redis_client, project_id)
        
        try:
            await notifier.publish("Regenerating article...")
            
            state: GraphState = {
                "project_id": project_id,
                "creator_id": cast(int, project.owner_id) if project and project.owner_id else 0,
                "keywords": [k.keyword for k in project.keywords] if hasattr(project, "keywords") else [],
                "industry": str(project.industry or ""),
                "rag_context": None,
                "search_queries": [],
                "current_articles": [],
                "retries": 0,
                "approved_articles": [{
                    "title": str(article.title or ""),
                    "url": str(article.url or ""),
                    "summary": str(article.summary or ""),
                    "source": str(article.source or ""),
                    "published_date": article.published_date.isoformat() if article.published_date else ""
                }],
                "generated_slides": {},
                "approved_slides": {},
                "publish_status": ""
            }
            
            await notifier.publish("Agent 'generate' is working...")
            state = content_generation_agent(state)
            
            await notifier.publish("Agent 'verify_slides' is working...")
            state = slide_verification_agent(state)
            
            approved_slides = state.get("approved_slides", {}).get(str(article.url), [])
            if not approved_slides:
                raise RuntimeError("Slide generation failed validation.")
            
            # Delete old slides
            for old_slide in list(article.slides):
                await db.delete(old_slide)
            
            # Insert new slides
            for i, slide_data in enumerate(approved_slides):
                slide = Slide(
                    article_id=article.id,
                    order_index=i,
                    hook_type=slide_data.get("hook_type", ""),
                    text_content=slide_data.get("text_content", ""),
                    caption=slide_data.get("caption", ""),
                    emoji=slide_data.get("emoji", "")
                )
                db.add(slide)
            
            article.status = "pending"
            await db.commit()
            await notifier.publish("Completed")
            
        except Exception as e:
            logger.exception(f"Regeneration for article {article_id} failed: {e}")
            if article:
                article.status = "pending"
                await db.commit()
            await notifier.publish("Failed", is_failed=True)


async def _render_slides_for_article(db, article, project) -> None:
    """Helper to render text onto background template for all slides of an article."""
    if not project.background_image_url:
        logger.warning(f"No background image URL set for project {project.id}, skipping render.")
        return

    slides_to_process = sorted(list(article.slides), key=lambda s: s.order_index)
    total_slides = len(slides_to_process)

    for idx, slide in enumerate(slides_to_process):
        strategy = SlideImageStrategyFactory.get_strategy(slide.visual_type)
        logger.info(f"Rendering slide {idx+1}/{total_slides} for article {article.id} using strategy {strategy.__class__.__name__}")
        try:
            url = await strategy.generate_and_save(db, slide, article, project, idx, total_slides)
            if url:
                slide.image_url = url
        except Exception as e:
            logger.error(f"Failed to generate/save slide image for slide {slide.id}: {e}")
            raise e
    
    article.status = "pending"
    await db.commit()


def run_image_generation_task(article_id: int):
    """Generates images using DALL-E 3 for the slides of a specific article."""
    asyncio.run(_run_image_generation_async(article_id))

async def _run_image_generation_async(article_id: int):
    async with worker_context() as (db, redis_client, _):
        result = await db.execute(
            select(Article)
            .options(selectinload(Article.project), selectinload(Article.slides))
            .where(Article.id == article_id)
        )
        article = result.scalar_one_or_none()
        
        if not article or not article.project_id:
            logger.error(f"Article {article_id} not found or missing project_id.")
            return

        project_id = cast(int, article.project_id)
        notifier = ProgressNotifier(redis_client, project_id)
        
        project = article.project
        if not project:
            logger.error(f"Project not found for article {article_id}")
            return

        try:
            if project.avoid_image_generation and not project.background_image_url:
                raise ValueError("Project background image is not uploaded yet.")

            logger.info(f"Starting slide image generation for article {article_id} (Avoid AI: {project.avoid_image_generation})")

            if project.avoid_image_generation:
                await notifier.publish("Rendering slide text onto background template...")
            else:
                await notifier.publish("Generating slide background images...")

            slides_to_process = sorted(list(article.slides), key=lambda s: s.order_index)
            total_slides = len(slides_to_process)

            for idx, slide in enumerate(slides_to_process):
                # [PATTERN: Strategy] - Resolve strategy per slide based on visual_type
                strategy = SlideImageStrategyFactory.get_strategy(slide.visual_type)
                logger.info(f"Processing slide {idx+1}/{total_slides} (ID: {slide.id}) using strategy {strategy.__class__.__name__}")
                await notifier.publish(f"Generating image for slide {idx+1}/{total_slides}...")

                url = await strategy.generate_and_save(db, slide, article, project, idx, total_slides)
                if url:
                    slide.image_url = url
                    await db.commit()
                else:
                    logger.warning(f"No image URL returned for slide {slide.id}")
            
            logger.info(f"Finished processing all slides for article {article_id}")
            article.status = "pending"
            await db.commit()
            
            await notifier.publish("Completed")
        except Exception as e:
            logger.error(f"Image generation task failed for article {article_id}: {str(e)}", exc_info=True)
            if article:
                article.status = "failed"
                await db.commit()
            await notifier.publish(f"Failed: {str(e)}", is_failed=True)
            raise e


def run_project_rerender_task(project_id: int):
    """Re-renders all pending slides of a project when the project background changes."""
    asyncio.run(_run_project_rerender_async(project_id))


async def _run_project_rerender_async(project_id: int):
    async with worker_context() as (db, redis_client, _):
        result = await db.execute(
            select(Project)
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project or not project.background_image_url:
            logger.error(f"Project {project_id} not found or missing background image.")
            return

        # Fetch all pending articles for this project
        articles_result = await db.execute(
            select(Article)
            .options(selectinload(Article.slides))
            .where(Article.project_id == project_id, Article.status == "pending")
        )
        articles = articles_result.scalars().all()
        
        notifier = ProgressNotifier(redis_client, project_id)
        await notifier.publish("Regenerating slide images with new background template...")
        
        for article in articles:
            await _render_slides_for_article(db, article, project)
            
        await notifier.publish("Completed")
