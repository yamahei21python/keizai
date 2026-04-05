# unified_pipeline.py (Modernized Python Version)
import os
import time
from typing import List, Dict
from keizai_scraper import KeizaiScraper

def main(limit: int = 10):
    print("=== AI Economic Report Pipeline (Modernized v5.0) ===")
    
    # フォルダ構成：reports/YYYYMMDD
    date_str = time.strftime("%Y%m%d")
    REPORTS_BASE = 'keizai-web/public/reports'
    REPORTS_SUBDIR = os.path.join(REPORTS_BASE, date_str)
    
    if not os.path.exists(REPORTS_SUBDIR):
        print(f"[*] Creating directory: {REPORTS_SUBDIR}")
        os.makedirs(REPORTS_SUBDIR)
    
    source_list_file = os.path.join(REPORTS_SUBDIR, 'notebooklm_links.txt')
    
    # Ranking URL for Macro Economy / Global (node=2)
    RANKING_URL = "http://www3.keizaireport.com/ranking.php/-/node=2/"
    
    results = []
    
    # 1. Start Scraper
    with KeizaiScraper(headless=True) as scraper:
        # Step 1: Fetch ranking
        print(f"[*] Phase 1: Fetching ranking from {RANKING_URL}...")
        all_reports = scraper.get_ranking_reports(RANKING_URL)
        
        # Filter and Take Top N
        report_list = []
        for r in all_reports:
            title = r['title']
            # Skip MOFA as per existing rule
            if "外務省" in title or "mofa" in r['jump_url'].lower():
                continue
            report_list.append(r)
            if len(report_list) >= limit:
                break
                
        print(f"[+] Processing top {len(report_list)} reports.")
        
        # Step 2: Resolve URLs
        for i, entry in enumerate(report_list, 1):
            title = entry['title']
            jump_url = entry['jump_url']
            
            print(f"[*] Processing Rank {i}: {title}")
            print(f"    - Resolving jump URL...")
            
            final_url = scraper.resolve_jump_url(jump_url)
            
            if final_url:
                results.append({"title": title, "url": final_url})
                print(f"    [+] Resolved: {final_url}")
            else:
                print(f"    [!] Failed to resolve for {title}")
            
            # Rate limiting as courtesy
            time.sleep(2)
            
    # Step 3: Output for NotebookLM
    if results:
        print(f"[*] Phase 3: Generating NotebookLM source list...")
        with open(source_list_file, 'w', encoding='utf-8') as f:
            f.write(f"--- Economic Report Sources ({time.strftime('%Y-%m-%d')}) ---\n\n")
            for res in results:
                f.write(f"[{res['title']}]\n")
                f.write(f"{res['url']}\n\n")
        
        print(f"\n[SUCCESS] NotebookLM source list generated: {source_list_file}")
        print("--- COPY & PASTE TO NOTEBOOKLM ---")
        for res in results:
            print(res['url'])
        print("----------------------------------")
    else:
        print("[!] No results obtained.")

if __name__ == "__main__":
    # You can adjust the limit for today's NRI focus or more.
    import sys
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    main(limit=limit_arg)
