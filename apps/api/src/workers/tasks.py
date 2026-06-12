import asyncio
import logging
import json
import redis.asyncio as redis

from db import session as db_session
from repositories.project import project_repo
from repositories.article import article_repo
from agents.graph import app_graph
from agents.state import GraphState
from core.config import get_settings

logger = logging.getLogger(__name__)

def get_progress_value(status: str) -> int:
    if status == "Not started": return 0
    if "Starting" in status: return 5
    if "research" in status: return 20
    if "verify" in status and "verify_slides" not in status: return 40
    if "refine" in status: return 45
    if "generate" in status: return 60
    if "verify_slides" in status: return 80
    if "publish" in status: return 95
    if status == "Completed": return 100
    return 10

def run_workflow_task(run_id: int):
    """
    Runs the LangGraph workflow for a given project synchronously (for RQ workers).
    Uses asyncio.run() since the RQ worker is synchronous by default but LangGraph/DB calls can be async.
    """
    asyncio.run(_run_workflow_async(run_id))

async def publish_progress(redis_client, project_id: int, status: str, is_failed: bool = False):
    progress = get_progress_value(status)
    payload = {
        "status": status,
        "progress": progress,
        "is_failed": is_failed
    }
    await redis_client.publish(f"workflow:progress:{project_id}", json.dumps(payload))

async def _run_workflow_async(run_id: int):
    settings = get_settings()
    redis_client = redis.from_url(settings.REDIS_URL)
    
    maker = db_session.async_session_maker or db_session.init_db()
    async with maker() as db:
        from models.core import WorkflowRun
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Fetch the workflow run
        result = await db.execute(select(WorkflowRun).options(selectinload(WorkflowRun.project)).where(WorkflowRun.id == run_id))
        workflow_run = result.scalar_one_or_none()
        
        if not workflow_run:
            logger.error(f"WorkflowRun {run_id} not found.")
            await redis_client.aclose()
            return

        project_id: int = workflow_run.project_id # type: ignore
        owner_id: int = workflow_run.project.owner_id # type: ignore

        # Fetch project with keywords
        project = await project_repo.get_with_keywords(db, id=project_id, owner_id=owner_id)
        if not project:
            logger.warning(f"Project {project_id} not found.")
            workflow_run.status = "Failed" # type: ignore
            workflow_run.error_message = f"Project {project_id} not found." # type: ignore
            await db.commit()
            await publish_progress(redis_client, project_id, "Failed", is_failed=True)
            await redis_client.aclose()
            return

        keywords = [kw.keyword for kw in project.keywords]
        
        # Initialize state
        initial_state: GraphState = {
            "project_id": project_id, # type: ignore
            "keywords": keywords,
            "industry": str(project.industry or ""),
            "search_queries": [],
            "current_articles": [],
            "retries": 0,
            "approved_articles": [],
            "generated_slides": {},
            "approved_slides": {},
            "publish_status": ""
        }
        
        try:
            workflow_run.status = "Starting workflow..." # type: ignore
            await db.commit()
            await publish_progress(redis_client, project_id, "Starting workflow...")
            
            # Use astream to track progress, then get final accumulated state
            final_state = None
            async for event in app_graph.astream(initial_state, stream_mode="values"):
                # In "values" mode, each event is the full accumulated state after a node runs
                final_state = event
                # Infer which node just ran from the status changes
                status_parts = []
                if event.get("current_articles"):
                    status_parts.append("research")
                if event.get("approved_articles"):
                    status_parts.append("verify")
                if event.get("generated_slides"):
                    status_parts.append("generate")
                if event.get("approved_slides"):
                    status_parts.append("verify_slides")
                if event.get("publish_status"):
                    status_parts.append("publish")
                
                latest_node = status_parts[-1] if status_parts else "starting"
                status_msg = f"Agent '{latest_node}' is working..."
                workflow_run.status = status_msg # type: ignore
                await db.commit()
                await publish_progress(redis_client, project_id, status_msg)

            if not final_state:
                raise RuntimeError("Workflow produced no output")

            logger.info(f"Workflow completed for project {project_id}. approved_articles={len(final_state.get('approved_articles', []))}, approved_slides={len(final_state.get('approved_slides', {}))}")
            
            # Save results to DB using the extracted repository logic
            await article_repo.save_workflow_results(db, project_id, final_state) # type: ignore
            logger.info(f"Persisted articles and slides to database for project {project_id}.")
            
            workflow_run.status = "Completed" # type: ignore
            await db.commit()
            await publish_progress(redis_client, project_id, "Completed")
            
        except Exception as e:
            logger.exception(f"Workflow {run_id} failed with error: {e}")
            workflow_run.status = "Failed" # type: ignore
            workflow_run.error_message = str(e) # type: ignore
            await db.commit()
            await publish_progress(redis_client, project_id, "Failed", is_failed=True)
        finally:
            await redis_client.aclose()


def run_article_regeneration_task(article_id: int):
    asyncio.run(_run_article_regeneration_async(article_id))

async def _run_article_regeneration_async(article_id: int):
    settings = get_settings()
    redis_client = redis.from_url(settings.REDIS_URL)
    
    maker = db_session.async_session_maker or db_session.init_db()
    async with maker() as db:
        from models.core import Article, Slide, Project
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(Article)
            .options(
                selectinload(Article.project).selectinload(Project.keywords),
                selectinload(Article.slides)
            )
            .where(Article.id == article_id)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            logger.error(f"Article {article_id} not found.")
            await redis_client.aclose()
            return

        project_id: int = article.project_id # type: ignore
        project = article.project
        
        try:
            await publish_progress(redis_client, project_id, "Regenerating article...")
            
            # Setup a mini GraphState
            state: GraphState = {
                "project_id": project_id, # type: ignore
                "keywords": [k.keyword for k in project.keywords] if hasattr(project, "keywords") else [],
                "industry": str(project.industry or ""),
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
            
            await publish_progress(redis_client, project_id, "Agent 'generate' is working...")
            from agents.nodes import content_generation_agent, slide_verification_agent
            
            # Run generation directly
            state = content_generation_agent(state)
            
            await publish_progress(redis_client, project_id, "Agent 'verify_slides' is working...")
            state = slide_verification_agent(state)
            
            # Check if we got approved slides
            approved_slides = state.get("approved_slides", {}).get(article.url, [])
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
            
            article.status = "pending" # Back to pending approval
            await db.commit()
            
            await publish_progress(redis_client, project_id, "Completed")
            
        except Exception as e:
            logger.exception(f"Regeneration for article {article_id} failed: {e}")
            article.status = "pending" # revert
            await db.commit()
            await publish_progress(redis_client, project_id, "Failed", is_failed=True)
        finally:
            await redis_client.aclose()
