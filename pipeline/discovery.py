from tools.serper_tool import fetch_live_leads
from tools.llm_tool import llm_call
import database.queries as db


# 🔍 EXISTING
def extract_entities_from_text(snippet, category, user_id): 
    prompt = f"""
    [TASK] Extract ONLY real business names from this text: "{snippet}"
    [RULES]
    - Return ONLY names separated by commas.
    - NO sentences, NO explanations.
    - If no clear business name exists, return 'None'.
    """
    
    response = llm_call(prompt, user_id)
    
    if not response or "None" in response or len(response) > 100:
        return []
        
    names = [name.strip() for name in response.split(",")]
    return [n for n in names if len(n.split()) < 5]



# -----------------------------
# 🧠 FEATURE DETECTION ENGINE
# -----------------------------
def detect_missing_features(website, name):
    issues = []

    site = (website or "").lower()

    # 🔥 Simple but effective checks
    if not site:
        issues.append("No Website")

    # You can later replace this with scraped content
    if "book" not in site and "appointment" not in site:
        issues.append("No Online Booking")

    if "whatsapp" not in site:
        issues.append("No WhatsApp Integration")

    if "chat" not in site:
        issues.append("No Live Chat")

    return issues


# -----------------------------
# 💰 REVENUE ESTIMATION
# -----------------------------
def estimate_revenue_loss(lead):
    rating = lead.get("rating", 0)

    # Base assumptions (simple for now)
    daily_visits = 20
    conversion_rate = 0.3
    avg_value = 500  # ₹ per visit

    # If low rating → worse conversion
    if rating and rating < 4:
        conversion_rate *= 0.7

    monthly_revenue = daily_visits * conversion_rate * avg_value * 30

    return int(monthly_revenue * 0.3)  # assume 30% loss


# -----------------------------
# 🎯 PRIORITY SCORING
# -----------------------------
def calculate_priority(lead, missing_features):
    score = 0

    rating = lead.get("rating", 0)

    # 🔥 Rating impact
    if rating and rating < 4:
        score += 3
    elif rating and rating < 4.3:
        score += 2

    # 🔥 Missing features impact
    score += len(missing_features)

    # 🔥 No website = strong signal
    if not lead.get("website"):
        score += 3

    # 🔥 No LinkedIn = weaker business
    if not lead.get("linkedin_url"):
        score += 1

    # -----------------------------
    # FINAL LABEL
    # -----------------------------
    if score >= 6:
        return "high"
    elif score >= 3:
        return "medium"
    return "low"


def run_sales_pipeline(user_input, user_id):
    if not user_input or len(user_input.strip()) < 3:
        return "⚠️ Invalid search query."

    clean_query = user_input.lower().replace("find", "").replace("search", "").strip()

    raw_data = fetch_live_leads(clean_query, user_id)
    places = raw_data.get("places", [])
    organic = raw_data.get("organic", [])

    # 🔁 Duplicate protection
    blacklist = set([url.lower().strip() for url in db.get_all_saved_urls(user_id) if url])

    final = []

    for lead in places:
        name = lead.get("title", "")
        name_lower = name.lower()

        website = lead.get("website", "")
        website_clean = website.lower().strip() if website else ""

        rating = lead.get("rating", 0)
        category = (lead.get("category") or "").lower()

        # -----------------------------
        # 🔓 LIGHT FILTERING (ONLY BAD STUFF)
        # -----------------------------
        combined = name_lower + " " + category

        # ❌ Remove clearly irrelevant businesses only
        if any(k in combined for k in ["hotel", "school", "college", "mall"]):
            continue

        # 🔁 Duplicate removal
        if website_clean and website_clean in blacklist:
            continue

        # 🧹 Basic sanity
        if not name or len(name.strip()) < 3:
            continue

        # -----------------------------
        # 🔗 LinkedIn detection
        # -----------------------------
        linkedin_url = ""
        for item in organic:
            link = item.get("link", "").lower()
            if "linkedin.com/company" in link:
                if name_lower.replace(" ", "") in link:
                    linkedin_url = item.get("link")
                    break

        # -----------------------------
        # 🧠 INTELLIGENCE LAYER
        # -----------------------------
        missing_features = detect_missing_features(website, name)

        revenue_loss = estimate_revenue_loss({
            "rating": rating
        })

        priority = calculate_priority({
            "rating": rating,
            "website": website,
            "linkedin_url": linkedin_url,
            "category": category
        }, missing_features)

        # -----------------------------
        # ✅ FINAL LEAD OBJECT
        # -----------------------------
        final.append({
            "name": name.strip(),
            "industry": clean_query,
            "website": website,
            "linkedin_url": linkedin_url,
            "desc": lead.get("address", ""),
            "analysis": "Click to Analyze",

            "missing_features": missing_features,
            "estimated_loss": revenue_loss,
            "priority": priority
        })

    if not final:
        return "⚠️ No leads found. Try a different location."

    db.add_to_history(user_id, user_input)

    return final[:9]