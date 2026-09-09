"""
Celery worker entry point.

Run with: celery -A backend.celery_worker.app worker --loglevel=info
Or directly: python backend/celery_worker.py
"""

from backend.workflow_engine.runner import app

if __name__ == "__main__":
    app.worker_main(["worker", "--loglevel=info", "--concurrency=2"])
