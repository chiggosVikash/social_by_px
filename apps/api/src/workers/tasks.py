import asyncio
from db import session as db_session
from repositories.project import project_repo
from agents.graph import app_graph
from agents.state import GraphState

def run_workflow_task(project_id: int):
    """
    Runs the LangGraph workflow for a given project synchronously (for RQ workers).
    Uses asyncio.run() since the RQ worker is synchronous by default but LangGraph/DB calls can be async.
    """
    asyncio.run(_run_workflow_async(project_id))

async def _run_workflow_async(project_id: int):
    maker = db_session.async_session_maker or db_session.init_db()
    async with maker() as db:
        # Fetch project with keywords
        project = await project_repo.get_with_keywords(db, id=project_id, owner_id=1) # Owner ID mocked as 1 for now
        if not project:
            print(f"Project {project_id} not found.")
            return

        keywords = [kw.keyword for kw in project.keywords]
        
        # Initialize state
        initial_state: GraphState = {
            "project_id": project_id,
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
        
        # We invoke the graph
        # Note: If graph relies on async nodes, invoke handles it, or use ainvoke
        final_state = await app_graph.ainvoke(initial_state)
        print(f"Workflow completed for project {project_id}. Final state keys: {final_state.keys()}")
        
        # Save results to DB
        from models.core import Article, Slide
        from sqlalchemy.future import select
        
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
                    status="approved"
                )
                db.add(article)
                await db.flush() # Get article.id
                
                slides_data = final_state.get("approved_slides", {}).get(article.url, [])
                for i, slide_data in enumerate(slides_data):
                    slide = Slide(
                        article_id=article.id,
                        order_index=i,
                        text_content=slide_data.get("text_content", "")
                    )
                    db.add(slide)
        
        await db.commit()
        print(f"Persisted articles and slides to database for project {project_id}.")
