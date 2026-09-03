import asyncio
import urllib.parse
import time
import json
import re
import os
from typing import Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from .models import Candidate, CandidateCriteria  

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

SAMPLE_CANDIDATES = [
    Candidate(profile_url="https://www.linkedin.com/in/ahmed-ali-backend-lead",
              full_name="Ahmed Ali", headline="Senior Python Backend Engineer",
              location="Cairo, Egypt", country="Egypt",
              current_role="Senior Backend Engineer", current_company="Vodafone Egypt",
              experience_years=7,
              skills=["Python","FastAPI","Django","PostgreSQL","AWS"],
              previous_roles=["Backend Engineer @ ITI","Python Developer @ Swvl"],
              education=["BSc Computer Science, Cairo University"],
              industries=["E-learning","Telecom"]),
    Candidate(profile_url="https://www.linkedin.com/in/fatima-zahra-mlops",
              full_name="Fatima Zahra", headline="ML Engineer | Ex-Siemens",
              location="Rabat, Morocco", country="Morocco",
              current_role="Machine Learning Engineer", current_company="Siemens",
              experience_years=5,
              skills=["Python","PyTorch","MLOps","Docker","GCP"],
              previous_roles=["Junior ML @ OCP"],
              education=["MSc AI, ENSIAS"],
              industries=["AI","Energy"]),
    Candidate(profile_url="https://www.linkedin.com/in/omar-haddad-fullstack",
              full_name="Omar Haddad", headline="Full-Stack Engineer | EdTech",
              location="Amman, Jordan", country="Jordan",
              current_role="Full-Stack Engineer", current_company="Abwaab",
              experience_years=4,
              skills=["Python","React","Node.js","MongoDB","Docker"],
              previous_roles=["Software Engineer @ Tamatem"],
              education=["BSc Software Eng, Jordan Univ. of Science & Tech"],
              industries=["E-learning","Gaming"]),
]

# 1. Generate MULTIPLE search queries combining different titles, locations, and skills
# 1. Generate MULTIPLE search queries combining different titles, locations, and skills
def build_google_queries(c: CandidateCriteria) -> list[str]:
    queries = []
    titles = c.titles if c.titles else [""]
    locations = c.locations if c.locations else [""]
    skills = c.skills if c.skills else [""]

    # 1. Precise Cartesian combinations
    for title in titles:
        for location in locations:
            for skill in skills:
                parts = ['site:linkedin.com/in']
                if title: parts.append(f'"{title}"')
                if location: parts.append(f'"{location}"')
                if skill: parts.append(f'"{skill}"')
                queries.append(" ".join(parts))

    # 2. Broader flexible queries
    for title in titles[:2]:
        for loc in locations[:2]:
            queries.append(f'site:linkedin.com/in {title} {loc}')
    for skill in skills[:3]:
        for loc in locations[:2]:
            queries.append(f'site:linkedin.com/in {skill} {loc}')

    # Remove duplicates and cap at 10 queries as requested
    unique_queries = list(dict.fromkeys(queries))
    return unique_queries[:10]
def fetch_profile_sync_authed(url: str, context) -> Optional[Candidate]:
    if "eg.linkedin.com" in url:
        clean_url = url.replace("eg.linkedin.com", "www.linkedin.com")
    elif "www.linkedin.com" not in url:
        clean_url = url.replace("linkedin.com", "www.linkedin.com")
    else:
        clean_url = url
    
    try:
        page = context.new_page()
        page.goto(clean_url, timeout=60000, wait_until="domcontentloaded")
        try:
            page.wait_for_function("document.title !== 'Join LinkedIn' && document.title !== ''", timeout=30000)
        except Exception:
            pass
        page.wait_for_timeout(9000)
        
        final_url = page.url
        page_title = page.title()
        
        # Check for Auth Wall OR if we accidentally landed on the Feed
        if "login" in final_url or "authwall" in final_url or "feed" in final_url:
            print("\n" + "="*50)
            print("🚨 AUTH WALL DETECTED! Waiting 15 seconds for login/session to establish...")
            print("="*50)
            
            # FIX: Wait 15 seconds automatically instead of waiting for ENTER
            time.sleep(15)
            
            # If the user was redirected to the Feed after login, force navigation BACK to the profile
            if clean_url not in page.url:
                print(f"[Thread] Navigating back to {clean_url}...")
                page.goto(clean_url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
                
            try:
                page.wait_for_function("document.title !== 'Join LinkedIn' && document.title !== ''", timeout=10000)
            except Exception:
                pass
                
            final_url = page.url
            page_title = page.title()
            
            # If we STILL aren't on the profile, abort this candidate
            if "authwall" in final_url or "login" in final_url or "feed" in final_url:
                print("  [FAILED] Still not on the profile page after 15s. Skipping this candidate.")
                page.close()
                return None

        name = page_title.replace("| LinkedIn", "").strip()
        visible_text = page.evaluate("document.body.innerText")
        page.close()

        if not name or not visible_text:
            return None

        return Candidate(
            profile_url=clean_url, 
            full_name=name, 
            summary=visible_text
        )
    except Exception:
        return None

def execute_real_scrape_sync(criteria: CandidateCriteria) -> list[Candidate]:
    # 2. Generate multiple queries
    queries = build_google_queries(criteria)
    print(f"[Thread] Generated {len(queries)} search queries.")
    
    profiles = []
    
    # Remove stale SingletonLock if exists to prevent Playwright crash
    lock_path = os.path.join("./li_browser_profile", "SingletonLock")
    if os.path.islink(lock_path) or os.path.exists(lock_path):
        try:
            os.unlink(lock_path)
        except Exception:
            pass

    headless_mode = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir="./li_browser_profile",
                headless=headless_mode,
                user_agent=UA,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """)
            
            page = context.new_page()
            print("[Thread] Checking LinkedIn session...")
            try:
                page.goto("https://www.linkedin.com/", timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
            except Exception as e:
                print(f"[Thread] LinkedIn check warning: {e}")
            
            if "login" in page.url or "signup" in page.url:
                print("\n[Thread] LinkedIn session not authenticated. Proceeding with Google & search queries...")
            
            print(f"[Thread] Searching with {len(queries)} queries (timeout 30s)...")
            
            all_urls = []
            consecutive_timeouts = 0
            
            # 3. Search for every query and collect all real LinkedIn profile URLs
            for q in queries:
                print(f"[Thread] Querying: {q}")
                
                try:
                    # Clean Google search without suspicious bot URL flags
                    page.goto(f"https://www.google.com/search?q={urllib.parse.quote(q)}&hl=en", timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)
                    
                    for btn_sel in ["button:has-text('Accept all')", "button:has-text('I agree')", "#L2AGLb", "button:has-text('Agree')"]:
                        try:
                            btn = page.locator(btn_sel)
                            if btn.count() > 0:
                                btn.first.click()
                                page.wait_for_timeout(2000)
                                break
                        except Exception:
                            pass

                    html_content = page.content()
                    found = re.findall(r'https?://(?:[a-z]{2}\.)?linkedin\.com/in/[A-Za-z0-9_%-]+', html_content)
                    
                    # Also parse /url?q= redirect links if wrapped by Google
                    for wrapped in re.findall(r'/url\?q=(https?://[^&]+)', html_content):
                        unquoted = urllib.parse.unquote(wrapped)
                        if "linkedin.com/in/" in unquoted:
                            found.append(unquoted)

                    for u in found:
                        clean_url = u.split("?")[0]
                        if clean_url.endswith("%23"): clean_url = clean_url[:-3]
                        clean_url = clean_url.rstrip("/")
                        
                        # Normalize URL to www. BEFORE checking for duplicates
                        if "eg.linkedin.com" in clean_url:
                            clean_url = clean_url.replace("eg.linkedin.com", "www.linkedin.com")
                        elif "www.linkedin.com" not in clean_url:
                            clean_url = clean_url.replace("linkedin.com", "www.linkedin.com")
                            
                        if clean_url not in all_urls and not clean_url.endswith("/in") and not clean_url.endswith("/sample-ahmed-ali"):
                            all_urls.append(clean_url)
                    
                    consecutive_timeouts = 0
                except Exception as e:
                    print(f"[Thread] Google query error: {e}")
                    consecutive_timeouts += 1
                    if consecutive_timeouts >= 2:
                        print("[Thread] Consecutive timeouts encountered on search network. Proceeding to profile processing...")
                        break
                    
                time.sleep(2)

            page.close()

            if not all_urls:
                print("[Thread] Google returned no URLs.")
                try: context.close()
                except: pass
                return []

            # 4. Slice to max_results
            all_urls = all_urls[:criteria.max_results]
            print(f"[Thread] Found {len(all_urls)} unique URLs. Scraping profiles...")
            
            for i, url in enumerate(all_urls):
                print(f"[Thread] Scraping ({i+1}/{len(all_urls)}): {url}")
                profile = fetch_profile_sync_authed(url, context)
                if profile:
                    print(f"[Thread]   -> Success: {profile.full_name}")
                    profiles.append(profile)
                time.sleep(2)
                
            try: context.close()
            except: pass
    except Exception as e:
        print(f"[Thread] Playwright scraping encountered error: {e}. Falling back to sample candidates.")

    return profiles
