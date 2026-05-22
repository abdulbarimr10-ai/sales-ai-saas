from flask import Blueprint, jsonify, request
from app.api.auth import require_auth
from database.models import supabase
from app.core.exceptions import APIError
from app.workers.celery_app import celery_app

jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')

@jobs_bp.route('', methods=['GET'])
@require_auth
def list_jobs():
    if not supabase:
        return jsonify({"status": "error", "message": "DB not initialized"}), 500
    
    # Get last 50 jobs for user
    response = supabase.table('job_runs').select('*').eq('user_id', request.user_id).order('created_at', desc=True).limit(50).execute()
    return jsonify({"status": "success", "data": response.data})

@jobs_bp.route('/<job_id>', methods=['GET'])
@require_auth
def get_job(job_id):
    if not supabase:
        return jsonify({"status": "error", "message": "DB not initialized"}), 500
        
    response = supabase.table('job_runs').select('*').eq('id', job_id).eq('user_id', request.user_id).execute()
    if not response.data:
        raise APIError("Job not found", status_code=404)
        
    return jsonify({"status": "success", "data": response.data[0]})

@jobs_bp.route('/cancel/<job_id>', methods=['POST'])
@require_auth
def cancel_job(job_id):
    # This requires Celery task ID tracking, which we can store in the 'metadata' field
    # For now, we will mark it as cancelled in DB so if it wakes up it aborts.
    if not supabase:
        return jsonify({"status": "error", "message": "DB not initialized"}), 500
        
    response = supabase.table('job_runs').select('*').eq('id', job_id).eq('user_id', request.user_id).execute()
    if not response.data:
        raise APIError("Job not found", status_code=404)
        
    # Mark in DB
    supabase.table('job_runs').update({'status': 'failed', 'error_message': 'Cancelled by user'}).eq('id', job_id).execute()
    
    # In a full implementation, read task_id from metadata and revoke in Celery:
    # metadata = response.data[0].get('metadata', {})
    # celery_task_id = metadata.get('celery_task_id')
    # if celery_task_id:
    #     celery_app.control.revoke(celery_task_id, terminate=True)
        
    return jsonify({"status": "success", "message": "Job cancelled."})
