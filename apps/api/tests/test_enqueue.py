import asyncio
from src.db import session
from src.models.core import WorkflowRun
from sqlalchemy import select
from src.workers.queue import enqueue_workflow

async def main():
    # Initialize DB
    session.init_db()
    
    async with session.async_session_maker() as db:
        # Get the latest WorkflowRun
        result = await db.execute(select(WorkflowRun).order_by(WorkflowRun.id.desc()).limit(1))
        latest_run = result.scalar_one_or_none()
        if not latest_run:
            print("No workflow runs found.")
            return
        
        print(f"Latest Workflow Run ID: {latest_run.id}")
        print(f"Status: {latest_run.status}")
        print(f"Enqueuing Workflow Run ID: {latest_run.id} to check if worker is running...")
        
        job = enqueue_workflow(latest_run.id)
        print(f"Job enqueued! Job ID: {job.id}")

if __name__ == "__main__":
    asyncio.run(main())
