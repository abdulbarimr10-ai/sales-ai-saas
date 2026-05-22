from tools.llm_tool import llm_call

def generate_hyper_personalized_email(lead, user_id):
    """
    Generates a high-conversion email based on priority-driven tone.
    """

    problem = lead.get('detected_problem', "manual processes")
    priority = lead.get('priority', "low")
    rating = lead.get('google_rating', 0)
    name = lead.get('name', "your clinic")
    missing = lead.get("missing_features", [])
    loss = lead.get("estimated_loss", 0)

    # 🔥 FORCE tone based on priority
    if priority == "high":
        tone_instruction = """
        - Be direct and specific
        - Highlight lost patients or revenue
        - Make problem feel urgent
        - Slightly bold but still professional
        """
        example_style = "You're likely losing patients due to..."

    elif priority == "medium":
        tone_instruction = """
        - Focus on improvement opportunity
        - Suggest optimization
        - Balanced tone (not aggressive)
        """
        example_style = "You could improve patient bookings by..."

    else:
        tone_instruction = """
        - Keep it light and friendly
        - No strong problem statements
        - Present as helpful idea
        """
        example_style = "Sharing a quick idea that might help..."

    prompt = f"""
    [ROLE] Senior Sales Strategist

    [TARGET] {name}

    [DATA]
    Problem: {problem}
    Google Rating: {rating}/5
    Priority: {priority}
    Missing Features: {missing}
    Estimated Monthly Loss: ₹{loss}

    [TONE RULES]
    {tone_instruction}

    [WRITING STYLE]
    Start similar to: "{example_style}"

    [TASK]
    Write a short, human-like cold email.

    STRUCTURE:
    1. Hook (specific to business)
    2. Mention the problem naturally
    3. Explain AI solution simply
    4. Low-pressure CTA

    [CONSTRAINTS]
    - Max 80 words
    - No generic phrases
    - No "Dear Sir/Madam"
    - Keep it natural and conversational
    """

    return llm_call(prompt, user_id)

def calculate_lead_roi(lead, user_id):
    """
    AI Consultant Tool: Analyzes industry and description to 
    generate a specific, data-backed ROI prediction.
    """
    prompt = f"""
    [ROLE] Expert AI Business Consultant
    [CONTEXT] 
    Company: {lead['name']}
    Industry: {lead['industry']}
    AI Strategy: {lead.get('analysis', 'General Automation')}

    [TASK] 
    Generate a one-sentence "ROI Metric" that proves why they need AI. 
    Focus on time saved, money saved, or revenue increased.

    [CONSTRAINTS]
    - Maximum 8 words.
    - Use numbers/percentages (e.g., 40% faster, 20 hrs/week).
    - Be professional and industry-specific.

    [OUTPUT EXAMPLE]
    - "Reduces customer support response time by 75%."
    - "Saves 15 hours weekly on manual data entry."
    """
    
    # We use our polished llm_call with the user_id for API key selection
    result = llm_call(prompt, user_id)
    return result.strip() if result else "High ROI potential detected."
