import asyncio
import logging

from db import session as db_session
from repositories.project import project_repo
from repositories.article import article_repo
from agents.graph import app_graph
from agents.state import GraphState

logger = logging.getLogger(__name__)

def run_workflow_task(run_id: int):
    """
    Runs the LangGraph workflow for a given project synchronously (for RQ workers).
    Uses asyncio.run() since the RQ worker is synchronous by default but LangGraph/DB calls can be async.
    """
    asyncio.run(_run_workflow_async(run_id))

async def _run_workflow_async(run_id: int):
    maker = db_session.async_session_maker or db_session.init_db()
    async with maker() as db:
        from models.core import WorkflowRun
        from sqlalchemy import select
        
        # Fetch the workflow run
        result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
        workflow_run = result.scalar_one_or_none()
        
        if not workflow_run:
            logger.error(f"WorkflowRun {run_id} not found.")
            return

        project_id: int = workflow_run.project_id # type: ignore

        # Fetch project with keywords
        project = await project_repo.get_with_keywords(db, id=project_id, owner_id=1) # [YAGNI-WARN] Owner ID mocked as 1 for now
        if not project:
            logger.warning(f"Project {project_id} not found.")
            workflow_run.status = "Failed" # type: ignore
            workflow_run.error_message = f"Project {project_id} not found." # type: ignore
            await db.commit()
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
            
            final_state = initial_state
            async for event in app_graph.astream(initial_state, stream_mode="updates"):
                # The event contains a mapping of node_name -> state_update
                for node_name, state_update in event.items():
                    logger.info(f"Agent '{node_name}' finished processing for project {project_id}.")
                    workflow_run.status = f"Agent '{node_name}' is working..." # type: ignore
                    await db.commit()
                    
                    # Update final_state with the latest updates from this node
                    final_state = {**final_state, **state_update}

            logger.info(f"Workflow completed for project {project_id}. Final state keys: {final_state.keys()}")
            
            # Save results to DB using the extracted repository logic
            await article_repo.save_workflow_results(db, project_id, final_state) # type: ignore
            logger.info(f"Persisted articles and slides to database for project {project_id}.")
            
            workflow_run.status = "Completed" # type: ignore
            await db.commit()
            
        except Exception as e:
            logger.exception(f"Workflow {run_id} failed with error: {e}")
            workflow_run.status = "Failed" # type: ignore
            workflow_run.error_message = str(e) # type: ignore
            await db.commit()
