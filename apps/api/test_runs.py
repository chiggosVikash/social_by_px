import asyncio
from db.session import async_session_maker
from models.core import WorkflowRun
from sqlalchemy import select

async def main():
    async with async_session_maker() as d:
        res = await d.execute(select(WorkflowRun))
        for r in res.scalars().all():
            print(f"ID: {r.id}, Status: {r.status}, Error: {r.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
