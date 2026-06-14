import asyncio
from db.session import init_db
from models.core import WorkflowRun
from sqlalchemy import text
from workers.tasks import _run_workflow_async, run_workflow_task

async def main():
    maker = init_db()
    async with maker() as db:
        # Create a run
        run = WorkflowRun(project_id=1, status="test")
        db.add(run)
        await db.commit()
        await db.refresh(run)
        print("Created run_id:", run.id)
        return run.id

if __name__ == "__main__":
    run_id = asyncio.run(main())
    try:
        run_workflow_task(run_id)
    except Exception as e:
        print("EXCEPTION:", e)
    
    async def check():
        maker = init_db()
        async with maker() as db:
            res = await db.execute(text(f"SELECT status, error_message FROM workflow_runs WHERE id={run_id}"))
            print("After:", res.fetchall())
    
    asyncio.run(check())
