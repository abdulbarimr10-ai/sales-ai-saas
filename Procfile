web: gunicorn "run:app" --workers 1 --timeout 120 --bind 0.0.0.0:${PORT:-5000}
celery_worker: celery -A app.workers.celery_app worker --loglevel=info -Q outreach,ai,emails,enrichment,maintenance -c 4
celery_beat: celery -A app.workers.celery_app beat --loglevel=info
flower: python -m app.workers.run_flower
