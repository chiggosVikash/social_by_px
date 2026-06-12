import redis
from rq import Queue
from core.config import get_settings

settings = get_settings()

redis_conn = redis.from_url(settings.REDIS_URL)

# High priority queue for workflow orchestration
workflow_queue = Queue('workflow', connection=redis_conn)

# Default queue for rendering and publishing
default_queue = Queue('default', connection=redis_conn)

def enqueue_workflow(run_id: int):
    """Enqueues a new workflow execution for a given workflow run."""
    # Importing here to avoid circular imports if needed
    from workers.tasks import run_workflow_task
    job = workflow_queue.enqueue(run_workflow_task, run_id)
    return job.id
