from flask import Blueprint, request, jsonify
from app.services.key_service import key_service
from app.models.api_key import ApiKeyCreateRequest
from pydantic import ValidationError
from app.core.exceptions import APIError, UnauthorizedError
from app.api.auth import require_auth
from database.models import supabase

keys_bp = Blueprint('keys', __name__, url_prefix='/api/keys')

@keys_bp.route('', methods=['GET'])
@require_auth
def get_keys():
    try:
        keys = key_service.get_user_keys(request.user_id)
        return jsonify({"status": "success", "data": keys})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "data": []}), 500

@keys_bp.route('', methods=['POST'])
@require_auth
def add_key():
    try:
        data = ApiKeyCreateRequest(**request.json)
    except ValidationError as e:
        raise APIError(str(e), status_code=400)
        
    try:
        record = key_service.save_api_key(request.user_id, data.provider, data.api_key)
        return jsonify({"status": "success", "message": "Key securely stored."})
    except ValueError as e:
        raise APIError(str(e), status_code=400)

@keys_bp.route('/<provider>', methods=['PUT'])
@require_auth
def update_key(provider):
    data = request.json
    api_key = data.get('api_key')
    if not api_key:
        raise APIError("api_key is required", status_code=400)
        
    try:
        validated_provider = ApiKeyCreateRequest(provider=provider, api_key=api_key).provider
        key_service.save_api_key(request.user_id, validated_provider, api_key)
        return jsonify({"status": "success", "message": "Key securely updated."})
    except (ValueError, ValidationError) as e:
        raise APIError(str(e), status_code=400)

@keys_bp.route('/<provider>', methods=['DELETE'])
@require_auth
def delete_key(provider):
    key_service.delete_key(request.user_id, provider)
    return jsonify({"status": "success", "message": "Key deleted successfully."})

@keys_bp.route('/test/<provider>', methods=['POST'])
@require_auth
def test_key(provider):
    decrypted_key = key_service.get_decrypted_key(request.user_id, provider)
    if not decrypted_key:
        raise APIError("No active key found for provider.", status_code=404)
        
    # Phase 5: Test using the LLMFactory
    from app.services.llm.factory import LLMFactory
    try:
        provider_instance = LLMFactory.get_provider(provider, request.user_id)
        is_valid = provider_instance.validate_key()
        if is_valid:
            return jsonify({"status": "success", "message": "Connection successful."})
        else:
            return jsonify({"status": "error", "message": "Connection failed."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@keys_bp.route('/usage', methods=['GET'])
@require_auth
def get_usage():
    if not supabase:
        return jsonify({"status": "error", "message": "DB not initialized"}), 500
        
    try:
        response = supabase.table('usage_tracking').select('*').eq('user_id', request.user_id).execute()
        return jsonify({"status": "success", "data": response.data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
