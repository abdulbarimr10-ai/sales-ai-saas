#apollo_tool.py

import requests
import database.queries as db


def enrich_with_apollo(company_name, domain=None, user_id=1):
    """
    Verified Apollo Enrichment with safety checks.
    Defaults to user_id 1 if context is missing.
    """
    # 1. Safe fetching of settings
    settings = db.get_user_settings(user_id)
    
    if not settings:
        print(f"⚠️ No settings found in DB for User {user_id}")
        return None

    # Use the exact column name from your database.py schema
    APOLLO_API_KEY = settings.get('apollo_api_key')
    
    if not APOLLO_API_KEY:
        print(f"❌ Apollo API Key missing for user {user_id}")
        return None

    url = "https://api.apollo.io/v1/organizations/enrich"
    
    params = {
        "api_key": APOLLO_API_KEY,
        "name": company_name
    }
    
    if domain:
        # Clean domain to ensure Apollo matches correctly
        clean_domain = domain.split("//")[-1].split("/")[0].replace("www.", "")
        params["domain"] = clean_domain

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json().get('organization', {})
            if not data: return None
            
            print(f"💎 Apollo found verified data for {company_name}")
            return {
                "website": data.get('website_url'),
                "linkedin_url": data.get('linkedin_url'),
                "industry": data.get('industry'),
                "estimated_num_employees": data.get('estimated_num_employees')
            }
    except Exception as e:
        print(f"❌ Apollo Request Failed: {e}")
    
    return None
