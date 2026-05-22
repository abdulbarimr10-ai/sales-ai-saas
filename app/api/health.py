from flask import Blueprint, jsonify
from app.core.logging import logger

health_bp = Blueprint('health', __name__)

@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    logger.info("Health check requested")
    return jsonify({
        "status": "ok",
        "message": "Sales AI API is running properly."
    }), 200
