#llm_tool.py
from app.services.llm.manager import llm_manager

def llm_call(prompt, user_id):
    """
    Proxies to the new LLMManager which securely orchestrates BYOK multi-provider routing,
    failovers, token tracking, and cost calculation.
    """
    return llm_manager.generate(prompt, user_id, request_type='general_llm_call')
