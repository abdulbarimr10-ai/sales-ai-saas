#linkedin_tool.py

import requests
import database.queries as db


def deep_search_linkedin(business_name, user_id):
    """Targeted search for LinkedIn if the initial search missed it."""
    settings = db.get_user_settings(user_id)
    api_key = settings.get('serper_api_key')
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    query = f'site:linkedin.com/company "{business_name}"'
    res = requests.post("https://google.serper.dev/search", headers=headers, json={"q": query})
    organic = res.json().get('organic', [])
    
    if organic:
        return organic[0].get('link', '')
    return ""
