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
    job = workflow_queue.enqueue(run_workflow_task, run_id, job_timeout=600)
    return job.id

def enqueue_article_regeneration(article_id: int):
    """Enqueues a background task to regenerate slides for an article."""
    from workers.tasks import run_article_regeneration_task
    job = workflow_queue.enqueue(run_article_regeneration_task, article_id, job_timeout=600)
    return job.id

def enqueue_image_generation(article_id: int):
    """Enqueues a background task to generate images for slides of an article."""
    from workers.tasks import run_image_generation_task
    job = workflow_queue.enqueue(run_image_generation_task, article_id, job_timeout=700)
    return job.id

def enqueue_project_rerender(project_id: int):
    """Enqueues a background task to (re-)render pending slides for a project."""
    from workers.tasks import run_project_rerender_task
    job = workflow_queue.enqueue(run_project_rerender_task, project_id, job_timeout=600)
    return job.id
