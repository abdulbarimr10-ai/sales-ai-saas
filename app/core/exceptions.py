from flask import jsonify

class APIError(Exception):
    """Base class for custom API errors"""
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['status'] = 'error'
        rv['message'] = self.message
        return rv

class UnauthorizedError(APIError):
    def __init__(self, message="Unauthorized"):
        super().__init__(message, status_code=401)

class NotFoundError(APIError):
    def __init__(self, message="Not Found"):
        super().__init__(message, status_code=404)

class ServerError(APIError):
    def __init__(self, message="Internal Server Error"):
        super().__init__(message, status_code=500)

def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"status": "error", "message": "An internal server error occurred"}), 500
