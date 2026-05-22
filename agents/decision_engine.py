from tools.llm_tool import llm_call


def audit_decision_agent(lead, user_id):
    """
    Hybrid Decision Engine:
    1. Fast rule-based decisions
    2. LLM fallback for smarter reasoning
    """

    website = lead.get("website")
    linkedin = lead.get("linkedin_url")
    rating = lead.get("google_rating", 0)

    # 🔥 STEP 1: SIMPLE RULES (FAST PATH)
    if website and linkedin:
        return {
            "use_apollo": False,
            "scrape_website": True,
            "find_linkedin": False,
            "source": "rules"
        }

    # 🔥 STEP 2: LLM DECISION (SMART PATH)
    prompt = f"""
    You are an AI decision engine for lead enrichment.

    Lead Data:
    - Website: {website}
    - LinkedIn: {linkedin}
    - Rating: {rating}

    Decide which actions are needed:

    1. use_apollo (for enrichment)
    2. scrape_website (if useful)
    3. find_linkedin (if missing)

    Return ONLY JSON:
    {{
        "use_apollo": true/false,
        "scrape_website": true/false,
        "find_linkedin": true/false
    }}
    """

    response = llm_call(prompt, user_id)

    if not response:
        print("⚠️ LLM failed → fallback to rules")
        return {
            "use_apollo": True,
            "scrape_website": bool(website),
            "find_linkedin": not linkedin,
            "source": "fallback"
        }

    # 🔥 STEP 3: SAFE PARSE
    try:
        import json
        parsed = json.loads(response)

        return {
            "use_apollo": parsed.get("use_apollo", True),
            "scrape_website": parsed.get("scrape_website", bool(website)),
            "find_linkedin": parsed.get("find_linkedin", not linkedin),
            "source": "llm"
        }

    except Exception as e:
        print(f"❌ LLM parse failed: {e}")

        return {
            "use_apollo": True,
            "scrape_website": bool(website),
            "find_linkedin": not linkedin,
            "source": "fallback"
        }