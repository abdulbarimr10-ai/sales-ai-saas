def audit_decision_agent(lead):
    """
    Decides which tools to use for this lead.
    Keeps it simple, explainable, and fast.
    """

    actions = {
        "use_apollo": False,
        "scrape_website": False,
        "find_linkedin": False
    }

    # 🧠 Rule 1: No website → try Apollo
    if not lead.get("website"):
        actions["use_apollo"] = True
    else:
        actions["scrape_website"] = True

    # 🧠 Rule 2: No LinkedIn → search
    if not lead.get("linkedin_url"):
        actions["find_linkedin"] = True

    return actions