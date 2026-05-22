#audit_flow.py

import requests
import json
from tools.llm_tool import llm_call
from tools.scraper_tool import scrape_website_content
from tools.apollo_tool import enrich_with_apollo
from tools.linkedin_tool import deep_search_linkedin
import database.queries as db
from agents.audit_agent import audit_decision_agent



def parse_problem_output(problem_text):
    """Convert text into structured data"""

    try:
        # Split into parts
        main, fix = problem_text.split("|")
        problem_part, impact = main.split(":")

        problem_type_map = {
            "Zero Online Presence": "zero_presence",
            "Reputation Loss": "reputation_loss",
            "No Booking System": "no_booking",
            "Missed Patient Leads": "missed_leads",
            "Slow Response": "slow_response",
            "Manual Operations": "manual_ops",
            "Weak Follow-up": "weak_followup"
        }

        problem_label = problem_part.strip()
        problem_type = problem_type_map.get(problem_label, "general")

        return {
            "type": problem_type,
            "label": problem_label,
            "impact": impact.strip(),
            "fix": fix.strip()
        }

    except:
        return {
            "type": "unknown",
            "label": "General Issue",
            "impact": problem_text,
            "fix": "Automation recommended"
        }
    
def calculate_lead_score(has_website, low_rating, has_booking):
    score = 0

    if not has_website:
        score += 50   # very high pain

    if low_rating:
        score += 30   # strong signal

    if not has_booking:
        score += 25   # conversion issue

    return score
    

def calculate_confidence(has_website, low_rating, has_booking):
    score = 50

    if not has_website:
        score += 30
    if low_rating:
        score += 25
    if not has_booking:
        score += 20

    return min(score, 95)

def assign_priority(problem_text):
    if not problem_text:
        return "low"

    if "Zero Online Presence" in problem_text:
        return "high"
    if "Reputation Loss" in problem_text:
        return "high"
    if "Missed Patient Leads" in problem_text:
        return "high"
    if "No Booking System" in problem_text:
        return "medium"

    return "low"

def deep_audit_business(business_name, website, user_id):
    """Hybrid Pain Detection: Rule-based + LLM reasoning"""

    settings = db.get_user_settings(user_id)
    api_key = settings.get('serper_api_key')

    url = "https://google.serper.dev/places"
    payload = json.dumps({"q": business_name})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}

    # 🔹 Default values
    rating = 0.0
    reviews_text = ""

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        places = response.json().get('places', [])

        if places:
            rating = places[0].get('rating', 0.0)
            reviews = places[0].get('reviews', [])
            
            # Extract few review snippets (safe)
            reviews_text = " ".join([r.get("snippet", "") for r in reviews[:3]])

    except Exception as e:
        print(f"❌ Serper error: {e}")

    # 🔥 RULE SIGNALS
    has_website = bool(website)
    low_rating = rating < 4.2

    # 🔥 WEBSITE ANALYSIS (lightweight)
    website_content = ""
    has_booking = False

    if has_website:
        web_data = safe_scrape_website(website)
        website_content = web_data.get("content", "").lower()

        if any(k in website_content for k in ["book", "appointment", "schedule"]):
            has_booking = True

    # 🔥 RULE-BASED PRIORITY LOGIC
    if not has_website:
        return {
            "rating": rating,
            "problem": "Zero Online Presence: Patients cannot find you | Build website + booking system"
        }

    if low_rating:
        return {
            "rating": rating,
            "problem": "Reputation Loss: Patients leaving due to poor experience | Automate feedback + follow-ups"
        }

    if not has_booking:
        return {
            "rating": rating,
            "problem": "No Booking System: Patients drop before scheduling | Add instant booking bot"
        }

    # 🔥 LLM REASONING (ONLY IF RULES NOT TRIGGERED)
    audit_prompt = f"""
    You are an expert in clinic automation.

    BUSINESS:
    {business_name}

    WEBSITE:
    {website_content[:800]}

    REVIEWS:
    {reviews_text}

    TASK:
    Identify the SINGLE biggest patient conversion problem.

    RULES:
    - Keep it SHORT
    - Max 12 words per section
    - No long explanations
    - No paragraphs

    FORMAT STRICTLY:
    [Problem]: [Impact] | [AI Fix]

    EXAMPLE:
    Missed Patient Leads: Inquiries not converted | Auto WhatsApp follow-up

    OPTIONS:
    - Missed Patient Leads
    - Slow Response
    - Manual Operations
    - Weak Follow-up
    """
    diagnosis = llm_call(audit_prompt, user_id)

    if not diagnosis:
        diagnosis = "Manual Operations: Staff overloaded, automation needed"

    problem_text = diagnosis.strip()

# 🔥 Assign priority
    priority = assign_priority(problem_text)

    return {
        "rating": rating,
        "problem": problem_text,
        "priority": priority   # ✅ NEW FIELD (SAFE)
    }

def analyze_lead_with_ai(lead, user_id, audit_data=None):
    # 1. Scrape the website during analysis
    web_data = scrape_website_content(lead.get('website'))
    
    # 2. Build a much deeper prompt
    prompt = f"""
    ### ROLE: AI Business Consultant
    ### CONTEXT:
    Company: {lead['name']}
    Services Found on Site: {web_data['content']}
    Google Rating: {audit_data.get('rating') if audit_data else 'N/A'}
    Current Problem: {audit_data.get('problem') if audit_data else 'Manual Operations'}

    ### TASK:
    Analyze the 'Services Found on Site'. Identify ONE specific service they offer that could be 10x more profitable with AI (e.g., automated appointment reminders, AI-driven patient follow-ups, or 24/7 web chat for lead capture).

    ### OUTPUT:
    One professional sentence explaining the AI solution and its ROI.
    """
    
    strategy = llm_call(prompt, user_id)
    return {
        "strategy": strategy.strip() if strategy else "High automation potential.",
        "email": web_data['email']
    }


import concurrent.futures

def safe_scrape_website(url):
    if not url:
        return {"email": "", "content": ""}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(scrape_website_content, url)
        try:
            return future.result(timeout=5)  # ⏱ max 5 sec
        except Exception as e:
            print("⚠️ Scraper timeout:", e)
            return {"email": "", "content": ""}


def safe_linkedin_search(name, user_id):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(deep_search_linkedin, name, user_id)
        try:
            return future.result(timeout=5)  # ⏱ max 5 sec
        except Exception as e:
            print("⚠️ LinkedIn timeout:", e)
            return ""

def execute_universal_audit(db_id, user_id):

    lead = db.get_lead_by_id(db_id)
    if not lead:
        return None

    # 🔹 Clean name
    short_name = lead['name'].split("(")[0].split("-")[0].strip()

    # 🔥 STEP 1: Agent decides actions
    actions = audit_decision_agent(lead)
    print(f"🧠 Agent Decision ({actions.get('source')}): {actions}")

    # 🔹 Safe defaults
    web_data = {"email": "", "content": ""}
    linkedin_url = lead.get("linkedin_url")
    website = lead.get("website")

    # 🔥 STEP 2: Execute Actions

    # --- APOLLO ---
    if actions.get("use_apollo"):
        print("🔧 Using Apollo...")
        try:
            apollo_data = enrich_with_apollo(short_name, website, user_id=user_id)
            if apollo_data:
                website = apollo_data.get("website") or website
                linkedin_url = apollo_data.get("linkedin_url") or linkedin_url
        except Exception as e:
            print(f"⚠️ Apollo enrichment failed: {e}")

    # --- SCRAPER ---
    if actions.get("scrape_website") and website:
        print("🔧 Scraping website...")
        try:
            web_data = safe_scrape_website(website)
        except Exception as e:
            print(f"⚠️ Website scraping failed: {e}")

    # --- LINKEDIN ---
    if actions.get("find_linkedin") and not linkedin_url:
        print("🔧 Searching LinkedIn...")
        try:
            linkedin_url = safe_linkedin_search(short_name, user_id)
        except Exception as e:
            print(f"⚠️ LinkedIn search failed: {e}")
    # 🔥 STEP 3: Pain Detection
    try:
        audit_data = deep_audit_business(short_name, website or "", user_id)
    except Exception as e:
        print("❌ Audit failed:", e)
        audit_data = {
            "rating": 0.0,
            "problem": "Manual Audit Required."
        }

    # 🔥 STEP 4: Save results (single source of truth)
    db.update_lead_field(db_id, "website", website)
    db.update_lead_field(db_id, "linkedin_url", linkedin_url)
    db.update_lead_field(db_id, "outreach_email", web_data.get("email", ""))
    db.update_lead_field(db_id, "google_rating", audit_data["rating"])
    db.update_lead_field(db_id, "detected_problem", audit_data["problem"])
    db.update_lead_field(db_id, "analysis", audit_data["problem"])

    # 🔥 STEP 5: Return
    return {
        "id": db_id,
        "status": "success",
        "analysis": audit_data["problem"],
        "google_rating": audit_data["rating"],
        "detected_problem": audit_data["problem"],
        "linkedin_url": linkedin_url,
        "website": website,
        "outreach_email": web_data.get("email", "")
    }