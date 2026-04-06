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
        self.browser = self.pw.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        # ScraperAPI proxy config (if key is set)
        context_kwargs = dict(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            device_scale_factor=1,
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            permissions=["geolocation"],
            color_scheme="dark",
            extra_http_headers={
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "Upgrade-Insecure-Requests": "1"
            }
        )

        if self.scraperapi_key:
            print(f"[*] ScraperAPI key detected. Using proxy for WAF bypass.")
            context_kwargs["proxy"] = {
                "server": "http://proxy.scraperapi.com:8001",
                "username": "scraperapi",
                "password": self.scraperapi_key
            }
            context_kwargs["ignore_https_errors"] = True
        else:
            print("[!] No SCRAPERAPI_KEY found. Running without proxy.")

        self.context = self.browser.new_context(**context_kwargs)
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
        """Equivalent to fetch_ranking.scpt"""
        page = self._setup_page()
        # Increase timeout and wait Strategy for CI environments
        print(f"[*] Navigating to ranking page: {url}")
        try:
            import random
            time.sleep(random.uniform(1.0, 3.0)) # Random delay before navigation
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Simulate interaction
            self._human_interaction(page)
            
            print(f"[DEBUG] Page Title: {page.title()}")
            
            # Wait for report items to be visible with longer timeout
            page.wait_for_selector('a[href*="jump.php"]', timeout=60000)
        except Exception as e:
            print(f"[DEBUG] ERROR during ranking fetch: {str(e)}")
            print(f"[DEBUG] Final URL: {page.url}")
            print(f"[DEBUG] Page Content (Partial): {page.content()[:1000]}")
            page.screenshot(path="ranking_error.png")
            raise
        
        time.sleep(2)
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        jump_links = soup.select('a[href*="jump.php"]')
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
        page.close()
        return reports

    def resolve_jump_url(self, jump_url: str) -> Optional[str]:
        """Equivalent to resolve_jump.scpt but with Recursive Deep Discovery."""
        page = self._setup_page()
        print(f"[*] Resolving jump URL: {jump_url}")
        
        final_url = jump_url
        try:
            # 1. Access initial jump URL
            page.goto(jump_url, wait_until="load", timeout=30000)
            
            for attempt in range(5):
                time.sleep(3) 
                current_url = page.url
                print(f"    - Current Location [{attempt+1}]: {current_url}")

                if current_url.lower().endswith('.pdf'):
                    final_url = current_url
                    break
                if "keizaireport.com" not in current_url:
                    final_url = current_url
                    break
                
                # INTERMEDIARY: report.php
                if "/report.php/" in current_url:
                    print("    - Intermediary summary page detected. Clicking title link...")
                    try:
                        with page.context.expect_page(timeout=10000) as popup_info:
                            title_link = page.query_selector('h1 a')
                            if title_link:
                                title_link.click()
                                page = popup_info.value
                                page.wait_for_load_state("load")
                            else: break
                    except Exception as e:
                        if "Download is starting" in str(e):
                            print(f"    [+] Success: PDF Download started from popup.")
                            # Capture from error string
                            url_match = re.search(r'at "(.+)"', str(e))
                            if url_match: final_url = url_match.group(1)
                            break
                        break
                    continue

                # REDIRECTOR: jump.php / jump001.php
                if "jump" in current_url:
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    refresh_tag = soup.find('meta', attrs={'http-equiv': 'Refresh'})
                    if refresh_tag:
                        match = re.search(r'URL=(.+)', refresh_tag.get('content', ''), re.IGNORECASE)
                        if match:
                            target = match.group(1)
                            if not target.startswith('http'):
                                from urllib.parse import urljoin
                                target = urljoin(page.url, target)
                            print(f"    - Following meta-refresh to: {target}")
                            final_url = target # Pre-set
                            try:
                                page.goto(target, wait_until="load")
                            except Exception as e:
                                if "Download is starting" in str(e):
                                    final_url = target
                                    break
                                raise e
                            continue
                    
                    a_tag = soup.select_one('a[href^="http"]')
                    if a_tag:
                        target = a_tag.get('href')
                        print(f"    - Following redirect link to: {target}")
                        final_url = target # Pre-set
                        try:
                            page.goto(target, wait_until="load")
                        except Exception as e:
                            if "Download is starting" in str(e):
                                final_url = target
                                break
                            raise e
                        continue
            
            # Only update final_url from page.url if we haven't already captured a better target
            if "keizaireport.com" in final_url:
                final_url = page.url

        except Exception as e:
            if "Download is starting" in str(e):
                print(f"    [+] Success: Direct PDF download detected.")
                url_match = re.search(r'at "(.+)"', str(e))
                if url_match: final_url = url_match.group(1)
            else:
                print(f"    [!] Error resolving jump: {e}")
                final_url = page.url
        
        try:
            final_url = final_url or page.url
            if "keizaireport.com" in final_url or not final_url.lower().endswith('.pdf'):
                if "keizaireport.com" not in final_url and not final_url.lower().endswith('.pdf'):
                    print("    - Landed on external HTML page. Searching for direct PDF link...")
                    pdf_link = self._find_pdf_link(page)
                    if pdf_link:
                        print(f"    [+] Deep Discovery found PDF: {pdf_link}")
                        final_url = pdf_link
            
            print(f"[+] Final Discovery: {final_url}")
            return final_url
        except Exception:
            return final_url
        finally:
            page.close()

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
