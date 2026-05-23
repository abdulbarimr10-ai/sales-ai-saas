from flask import Flask, request, jsonify
from flask_cors import CORS
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_error_handlers
import os

def create_app():
    """Application factory for the Sales AI platform."""
    # 1. Setup logging
    logger = setup_logging()
    logger.info("Starting Sales AI Platform initialization...")

    # 2. Initialize Flask App
    # Setting template and static folders to support existing frontend integration
    app = Flask(
        __name__,
        template_folder="../../frontend/dist",
        static_folder="../../frontend/dist/assets",
        static_url_path="/assets"
    )

    # 3. Apply Configuration
    app.config.from_mapping(
        SECRET_KEY=settings.SECRET_KEY,
        ENV=settings.ENV,
        DEBUG=settings.DEBUG,
    )

    # 4. Setup CORS (Cross-Origin Resource Sharing)
    CORS(
        app, 
        supports_credentials=True, 
        origins=settings.cors_origins,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # 5. Register Error Handlers
    register_error_handlers(app)

    # 5b. Additional error handler for 405 Method Not Allowed
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "status": "error", 
            "message": f"Method {request.method} not allowed for {request.path}"
        }), 405

    # 6. Register Blueprints
    from app.api.health import health_bp
    from app.api.keys import keys_bp
    from app.api.gmail import gmail_bp
    from app.api.auth import auth_bp
    from app.api.jobs import jobs_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(keys_bp)
    app.register_blueprint(gmail_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)

    # 7. Security Headers Middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;"
        return response

    # 8. Rate Limiting
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    # Deriving rate limiter storage URI from REDIS_URL and routing to DB 1 to avoid key collision
    import re
    import redis
    redis_url_limiter = settings.REDIS_URL
    
    if redis_url_limiter and not redis_url_limiter.startswith("memory://"):
        if re.search(r'/\d+$', redis_url_limiter):
            redis_url_limiter = re.sub(r'/\d+$', '/1', redis_url_limiter)
        else:
            redis_url_limiter = redis_url_limiter.rstrip('/') + '/1'
            
        try:
            # Test connection to Redis
            test_client = redis.Redis.from_url(redis_url_limiter)
            test_client.ping()
            logger.info("Limiter: Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"Limiter: Could not connect to Redis at {redis_url_limiter}: {e}. Falling back to in-memory rate limiting.")
            redis_url_limiter = "memory://"
    else:
        logger.warning("Limiter: No REDIS_URL configured or set to memory://. Falling back to in-memory rate limiting.")
        redis_url_limiter = "memory://"

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=redis_url_limiter
    )
    # Apply specific limits to auth
    limiter.limit("5 per minute")(auth_bp)
    
    # Register legacy server routes temporarily to maintain backward compatibility
    try:
        from app.server import legacy_bp
        app.register_blueprint(legacy_bp)
        logger.info("Legacy blueprint registered successfully.")
    except ImportError as e:
        logger.warning(f"Could not load legacy blueprint: {e}")

    logger.info("Application factory completed successfully.")
    return app
