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

        # Launch browser without global proxy. We use per-context proxies.
        print("[*] Launching Playwright (Context-aware proxy configuration).")
        self.browser = self.pw.chromium.launch(**launch_kwargs)
        return self

    def _new_proxied_context(self) -> BrowserContext:
        """Create a new context with ScraperAPI's residential proxy."""
        kwargs = self._default_context_kwargs()
        if self.scraperapi_key:
            kwargs["proxy"] = {
                "server": "http://proxy-server.scraperapi.com:8001",
                "username": "scraperapi",
                "password": self.scraperapi_key
            }
        return self.browser.new_context(**kwargs)

    def _new_direct_context(self) -> BrowserContext:
        """Create a new context without any proxy."""
        return self.browser.new_context(**self._default_context_kwargs())

    def _default_context_kwargs(self) -> dict:
        """Common context parameters."""
        return {
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "viewport": {'width': 1280, 'height': 720},
            "device_scale_factor": 1,
            "locale": "ja-JP",
            "timezone_id": "Asia/Tokyo",
            "permissions": ["geolocation"],
            "color_scheme": "dark",
            "ignore_https_errors": True,
            "extra_http_headers": {
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Upgrade-Insecure-Requests": "1"
            }
        }

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()

    def get_ranking_reports(self, url: str) -> List[Dict]:
        """Fetch ranking via ScraperAPI API mode (render=false, 1 credit)."""
        import requests as req

        print(f"[*] Fetching ranking page via ScraperAPI (no JS rendering): {url}")

        if not self.scraperapi_key:
            raise ValueError("SCRAPERAPI_KEY is missing! Set it in .env or GitHub Secrets.")

        params = {
            "api_key": self.scraperapi_key,
            "url": url,
            "country_code": "jp",
            "keep_headers": "true" 
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": "http://www3.keizaireport.com/"
        }

        try:
            def _fetch():
                return req.get("https://api.scraperapi.com/", params=params, headers=headers, timeout=120)

            response = _fetch()
            response.raise_for_status()
            for retry in range(3):
                if len(response.text) > 1000: break 
                print(f"[DEBUG] Response too short ({len(response.text)} chars), retrying ({retry+1}/3)...")
                time.sleep(5)
                response = _fetch()
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

    def resolve_jump_url(self, jump_url: str, referer: Optional[str] = None) -> Optional[str]:
        """Resolve jump URL: Directly navigate to jump URL with Referer spoofing in a PROXIED context."""
        if not referer:
            referer = "http://www3.keizaireport.com/ranking.php/-/node=2/"

        print(f"[*] Resolving jump URL with Direct Proxied Jump Strategy: {jump_url}")
        
        current_external_url = None
        
        # Retry loop for proxied phase resilience
        for attempt in range(3):
            print(f"    - Resolution Attempt [{attempt+1}/3]...")
            context = self._new_proxied_context()
            page = context.new_page()
            stealth_sync(page)
            
            try:
                # 1. Spoof Referer to bypass WAF direct-access checks
                page.set_extra_http_headers({"Referer": referer})
                
                # 2. Directly navigate to the jump URL
                print(f"      - Directly navigating to jump page with Referer spoofing...")
                page.goto(jump_url, wait_until="domcontentloaded", timeout=90000)
                
                # 3. Redirection / Link Extraction
                print(f"      - Redirection monitoring (Currently at {page.url})...")
                for _ in range(12): 
                    # If we already left the domain, we are done
                    if "keizaireport.com" not in page.url:
                        current_external_url = page.url
                        break
                    
                    try:
                        # Priority: Look for '@@ こちら @@' or any cross-domain link
                        next_link = page.query_selector('a:has-text("@@ こちら @@")')
                        if not next_link:
                            next_link = page.query_selector('a[href^="http"]:not([href*="keizaireport.com"])')
                        
                        if next_link:
                            href = next_link.get_attribute("href")
                            if href and href.startswith("http"):
                                print(f"      - Found external URL ({next_link.inner_text().strip() or 'link'}): {href}")
                                current_external_url = href
                                break
                    except Exception:
                        pass
                    time.sleep(3)

                if current_external_url:
                    # Success!
                    break
                else:
                    print(f"      [!] Stalled or empty on keizaireport.com. Retrying with new proxy session...")

            except Exception as e:
                print(f"      [!] Proxied jump error: {e}. Retrying with new proxy session...")
            finally:
                context.close()

        if not current_external_url:
            print(f"    [!] Failed to resolve jump URL after 3 proxied attempts.")
            return jump_url

        # 4. Long-term discovery using DIRECT context (0 credits)
        print(f"    [+] Successfully reached external site: {current_external_url}")
        return self.find_pdf_on_external_site(current_external_url)

    def find_pdf_on_external_site(self, url: str) -> str:
        """PDF discovery using DIRECT Playwright (no proxy) with error resilience."""
        if url.lower().endswith('.pdf'): return url
        if not url.startswith('http'): return url

        print(f"[*] Switching to DIRECT Playwright for PDF discovery: {url}")
        
        # Simple retry loop for network stability
        for attempt in range(2):
            context = self._new_direct_context()
            page = context.new_page()
            stealth_sync(page)
            try:
                # Use domcontentloaded for faster check first
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                
                # Check for browser-level errors
                if "chrome-error://" in page.url:
                    print(f"    [!] Browser network error on attempt {attempt+1}. Retrying...")
                    continue
                
                time.sleep(2)
                
                # Search for PDF link
                js_script = "() => Array.from(document.querySelectorAll('a[href]')).map(a => ({ href: a.href, text: a.innerText.trim() }))"
                links = page.evaluate(js_script)
                keywords = ["PDF", "全文", "ダウンロード", "Download", "レポート", "Report", "表示"]
                
                pdf_url = None
                # 1. Exact PDF link with keywords
                for link in links:
                    if link['href'].lower().endswith('.pdf'):
                        if any(kw.upper() in link['text'].upper() for kw in keywords):
                            pdf_url = link['href']
                            break
                # 2. Any PDF link
                if not pdf_url:
                    for link in links:
                        if link['href'].lower().endswith('.pdf'):
                            pdf_url = link['href']
                            break
                # 3. Link containing 'pdf' in URL and keyword in text
                if not pdf_url:
                    for link in links:
                        if 'pdf' in link['href'].lower() and any(kw.upper() in link['text'].upper() for kw in keywords):
                            pdf_url = link['href']
                            break
                
                if pdf_url:
                    print(f"    [+] Deep Discovery found PDF: {pdf_url}")
                    return pdf_url
                
                return page.url
            except Exception as e:
                print(f"    [!] Direct discovery error on attempt {attempt+1}: {e}")
            finally:
                context.close()
        
        return url

    def capture_content(self, url: str) -> str:
        """Capture page content using DIRECT Playwright (no proxy)."""
        if url.lower().endswith('.pdf'): return "【注】PDFファイルのため、テキストのみのキャプチャはスキップされました。"
        
        print(f"[*] Capturing content via DIRECT Playwright: {url}")
        context = self._new_direct_context()
        page = context.new_page()
        stealth_sync(page)
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            time.sleep(2)
            
            # Simple JS capture
            js_capture = "() => { const text = document.body.innerText; const links = Array.from(document.querySelectorAll('a[href]')).map(a => a.href).filter(h => h.startsWith('http')).join('\\n'); return '--- CONTENT ---\\n' + text + '\\n\\n--- LINKS ---\\n' + links; }"
            return page.evaluate(js_capture)
        except Exception as e:
            return f"【エラー】{e}"
        finally:
            context.close()
