import time
import re
import os
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext
from playwright_stealth import stealth_sync
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

class KeizaiScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.pw = None
        self.browser = None
        self.context = None
        self.scraperapi_key = os.getenv("SCRAPERAPI_KEY")

    def __enter__(self):
        self.pw = sync_playwright().start()

        launch_kwargs = dict(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        if self.scraperapi_key:
            print("[*] ScraperAPI key detected. Using proxy for WAF bypass.")
            launch_kwargs["proxy"] = {
                "server": "http://proxy-server.scraperapi.com:8001",
                "username": "scraperapi",
                "password": self.scraperapi_key
            }
        else:
            print("[!] No SCRAPERAPI_KEY found. Running without proxy.")

        self.browser = self.pw.chromium.launch(**launch_kwargs)

        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            device_scale_factor=1,
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            permissions=["geolocation"],
            color_scheme="dark",
            ignore_https_errors=True,
            extra_http_headers={
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "Upgrade-Insecure-Requests": "1"
            }
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()

    def _setup_page(self) -> Page:
        page = self.context.new_page()
        # 1. Standard stealth package
        stealth_sync(page)
        
        # 2. Additional custom script overrides for headless detection
        page.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            
            // Override chrome.runtime
            window.chrome = {
              runtime: {},
              app: {},
              csi: () => {},
              loadTimes: () => {}
            };
            
            // Fix language and fonts
            Object.defineProperty(navigator, 'languages', { get: () => ['ja-JP', 'ja', 'en-US', 'en'] });
            
            // Mask WebGL context
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
              if (parameter === 37445) return 'Intel Inc.';
              if (parameter === 37446) return 'Intel(R) Iris(TM) Plus Graphics 640';
              return getParameter.apply(this, arguments);
            };
        """)
        return page

    def _human_interaction(self, page: Page):
        """Simulate subtle mouse movement and scroll to look more human."""
        import random
        try:
            viewport = page.viewport_size
            if viewport:
                # Move mouse to a random point
                x = random.randint(0, viewport['width'])
                y = random.randint(0, viewport['height'])
                page.mouse.move(x, y)
                # Subtle scroll
                page.mouse.wheel(0, random.randint(50, 200))
                time.sleep(random.uniform(0.5, 1.5))
        except Exception:
            pass

    def get_ranking_reports(self, url: str) -> List[Dict[str, str]]:
        """Fetch ranking via ScraperAPI API mode (render=false, 1 credit).

        The target site detects headless browsers and returns an empty body.
        Raw HTTP requests via ScraperAPI's residential proxy return the full HTML.
        """
        import requests as req

        print(f"[*] Fetching ranking page via ScraperAPI (no JS rendering): {url}")

        if not self.scraperapi_key:
            raise ValueError("SCRAPERAPI_KEY is missing! Set it in .env or GitHub Secrets.")

        params = {
            "api_key": self.scraperapi_key,
            "url": url,
            "country_code": "jp",
            # "premium": "true",  # Uncomment for premium IPs if still blocked (10 credits)
        }

        try:
            response = req.get("https://api.scraperapi.com/", params=params, timeout=120)
            response.raise_for_status()
            # Retry if response is truncated (ScraperAPI sometimes returns partial on first attempt)
            for retry in range(3):
                if len(response.text) > 200:
                    break
                print(f"[DEBUG] Response too short ({len(response.text)} chars), retrying ({retry+1}/3)...")
                time.sleep(3)
                response = req.get("https://api.scraperapi.com/", params=params, timeout=120)
                response.raise_for_status()
            content = response.text
            print(f"[DEBUG] Content length: {len(content)} chars")
        except Exception as e:
            print(f"[DEBUG] ScraperAPI request error: {e}")
            raise

        soup = BeautifulSoup(content, 'html.parser')
        jump_links = soup.select('a[href*="jump.php"]')
        print(f"[DEBUG] Found {len(jump_links)} jump links")

        reports = []
        for link in jump_links:
            href = link.get('href')
            rid_match = re.search(r'RID=(\d+)', href)
            if not rid_match: continue
            rid = rid_match.group(1)
            container = link.find_parent('div') or link.parent
            if '会員専用' in container.get_text(): continue
            title_link = soup.select_one(f'a.r_t[href*="/{rid}/"]')
            if title_link:
                title = title_link.get_text(strip=True)
                if not any(r['title'] == title for r in reports):
                    full_href = f"http://www3.keizaireport.com{href}" if href.startswith('/') else href
                    reports.append({"title": title, "jump_url": full_href})
        return reports

    def resolve_jump_url(self, jump_url: str) -> Optional[str]:
        """Resolve jump.php redirect chain via requests + ScraperAPI (no browser needed)."""
        import requests as req
        from urllib.parse import urljoin

        print(f"[*] Resolving jump URL: {jump_url}")
        current_url = jump_url

        session = req.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        })

        for attempt in range(8):
            print(f"    - Current Location [{attempt+1}]: {current_url}")

            # Escaped keizaireport.com URLs - follow via ScraperAPI
            if "keizaireport.com" in current_url:
                if self.scraperapi_key:
                    params = {"api_key": self.scraperapi_key, "url": current_url, "country_code": "jp"}
                    try:
                        resp = session.get("https://api.scraperapi.com/", params=params, timeout=60, allow_redirects=True)
                    except Exception as e:
                        print(f"    [!] Error: {e}")
                        break
                else:
                    try:
                        resp = session.get(current_url, timeout=30, allow_redirects=True)
                    except Exception as e:
                        print(f"    [!] Error: {e}")
                        break

                # Small responses mean truncated/empty - retry up to 3 times
                for retry in range(3):
                    if len(resp.text) > 200:
                        break
                    print(f"    - Response too short ({len(resp.text)} chars), retrying ({retry+1}/3)...")
                    time.sleep(2)
                    try:
                        if self.scraperapi_key:
                            resp = session.get("https://api.scraperapi.com/", params=params, timeout=60, allow_redirects=True)
                        else:
                            resp = session.get(current_url, timeout=30, allow_redirects=True)
                    except Exception:
                        break

                # If HTTP redirect landed outside keizaireport.com, we're done
                if "keizaireport.com" not in resp.url:
                    current_url = resp.url
                    print(f"    - HTTP redirect resolved to: {current_url}")
                    break

                # Check for meta-refresh redirect in response HTML
                soup = BeautifulSoup(resp.text, 'html.parser')
                refresh_tag = soup.find('meta', attrs={'http-equiv': re.compile('refresh', re.I)})
                if refresh_tag:
                    content_val = refresh_tag.get('content', '')
                    match = re.search(r'URL=(.+)', content_val, re.IGNORECASE)
                    if match:
                        target = match.group(1).strip().strip('"\'')
                        if not target.startswith('http'):
                            target = urljoin(current_url, target)
                        print(f"    - Following meta-refresh to: {target}")
                        current_url = target
                        continue

                # Check for JavaScript window.location.href (even if commented out)
                js_match = re.search(
                    r'window\.location\.href\s*=\s*["\']([^"\'\']+)["\']',
                    resp.text
                )
                if js_match:
                    target = js_match.group(1).strip()
                    print(f"    - Extracted JS redirect target: {target}")
                    current_url = target
                    continue

                # Check for <a href> redirect link on jump pages
                a_tag = soup.select_one('a[href^="http"]')
                if a_tag:
                    target = a_tag.get('href')
                    print(f"    - Following anchor redirect to: {target}")
                    current_url = target
                    continue

                # report.php intermediary: find title link
                if "/report.php/" in resp.url:
                    title_link = soup.select_one('h1 a[href]')
                    if title_link:
                        target = title_link.get('href')
                        if not target.startswith('http'):
                            target = urljoin(resp.url, target)
                        print(f"    - Following report.php title link to: {target}")
                        current_url = target
                        continue

                # No redirect found - stuck
                print(f"    [!] No redirect found in page. Content length: {len(resp.text)}")
                break

            else:
                # Already outside keizaireport.com - final destination reached
                break

        # If final URL is still a PDF, return as-is
        if current_url.lower().endswith('.pdf'):
            print(f"[+] Final Discovery (PDF): {current_url}")
            return current_url

        # If landed on external page, try to find a PDF link
        if "keizaireport.com" not in current_url and current_url != jump_url:
            try:
                if self.scraperapi_key:
                    params = {"api_key": self.scraperapi_key, "url": current_url, "country_code": "jp"}
                    resp = session.get("https://api.scraperapi.com/", params=params, timeout=60)
                else:
                    resp = session.get(current_url, timeout=30)
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if not href.startswith('http'):
                        href = urljoin(current_url, href)
                    if href.lower().endswith('.pdf'):
                        keywords = ["PDF", "全文", "ダウンロード", "Download", "レポート"]
                        if any(k.upper() in a.get_text().upper() for k in keywords):
                            print(f"    [+] Deep Discovery found PDF: {href}")
                            current_url = href
                            break
            except Exception as e:
                print(f"    [!] Deep discovery error: {e}")

        print(f"[+] Final Discovery: {current_url}")
        return current_url



    def _find_pdf_link(self, page: Page) -> Optional[str]:
        """Search for the best PDF link on the current landing page."""
        try:
            links = page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    href: a.href,
                    text: a.innerText.trim(),
                    title: a.title.trim()
                }))
            """)
            keywords = ["PDF", "全文", "ダウンロード", "Download", "レポート", "Report", "表示"]
            for link in links:
                href_lower = link['href'].lower()
                text_upper = link['text'].upper()
                if href_lower.endswith('.pdf'):
                    if any(kw.upper() in text_upper for kw in keywords): return link['href']
            for link in links:
                if link['href'].lower().endswith('.pdf'): return link['href']
            for link in links:
                if 'pdf' in link['href'].lower() or 'pdf' in link['text'].lower():
                    if any(kw.upper() in link['text'].upper() for kw in keywords): return link['href']
            return None
        except Exception: return None

    def capture_content(self, url: str) -> str:
        """Equivalent to capture_content.scpt"""
        page = self._setup_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(10)
            return page.evaluate("""
                () => {
                    let text = document.body.innerText;
                    let links = Array.from(document.querySelectorAll('a[href]'))
                                     .map(a => a.href)
                                     .filter(h => h.startsWith('http'))
                                     .join('\\n');
                    return '--- CONTENT ---\\n' + text + '\\n\\n--- LINKS ---\\n' + links;
                }
            """)
        except Exception as e: return f"【エラー】{e}"
        finally: page.close()
