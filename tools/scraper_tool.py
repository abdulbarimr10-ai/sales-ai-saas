#scraper_tool.py

import requests
from bs4 import BeautifulSoup
import re


def scrape_website_content(url):
    if not url or "http" not in url:
        return {"email": "", "content": ""}

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # ⏱️ Tightened timeout to 7 seconds total
        response = requests.get(url, headers=headers, timeout=7)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content = soup.get_text()
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
        
        if not emails:
            print(f"🔍 Checking sub-pages for {url}...")
            links = soup.find_all('a', href=True)
            # 🛑 LIMIT: Only check the first 3 relevant links to prevent freezing
            sub_links_to_check = []
            for link in links:
                href = link['href'].lower()
                if ('contact' in href or 'about' in href) and len(sub_links_to_check) < 3:
                    full_url = href if 'http' in href else url.rstrip('/') + '/' + href.lstrip('/')
                    sub_links_to_check.append(full_url)

            for sub_url in sub_links_to_check:
                try:
                    # ⏱️ Very fast check for sub-pages
                    res = requests.get(sub_url, headers=headers, timeout=4)
                    sub_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', res.text)
                    if sub_emails:
                        emails.extend(sub_emails)
                        print(f"✅ Found email on {sub_url}")
                        break 
                except:
                    continue

        found_email = list(set(emails))[0] if emails else ""
        return {
            "email": found_email,
            "content": content[:1500] # Slightly shorter to stay within LLM limits
        }
    except Exception as e:
        print(f"❌ Scraper timed out/failed: {e}")
        return {"email": "", "content": ""}
   