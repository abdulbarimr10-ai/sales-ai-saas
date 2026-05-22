#serper_tool.py

import requests
import database.queries as db



def fetch_live_leads(query, user_id):
    settings = db.get_user_settings(user_id)
    if not settings:
        print("❌ User settings not found. Cannot fetch leads.")
        return {"places": [], "organic": []}
    api_key = settings.get('serper_api_key')
    
    if not api_key:
        print("❌ API Key Missing")
        return {"places": [], "organic": []}

    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    try:
        # 1. Get real business entities (Places)
        p_res = requests.post("https://google.serper.dev/places", 
                             headers=headers, json={"q": query})
        
        # 2. Get organic results for LinkedIn extraction
        s_res = requests.post("https://google.serper.dev/search", 
                             headers=headers, json={"q": f"{query} linkedin company"})
        
        return {
            "places": p_res.json().get('places', []),
            "organic": s_res.json().get('organic', [])
        }
    except Exception as e:
        print(f"❌ Serper API Connection Failed: {e}")
        return {"places": [], "organic": []}
    
