# unified_pipeline.py (Master Intelligence Driver)
import os
import sys
import time
import subprocess
import re
from typing import List, Dict
from keizai_scraper import KeizaiScraper

def sanitize_filename(filename: str) -> str:
    """Remove platform-reserved characters and limit length."""
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    filename = filename.replace('\n', '').replace('\r', '').strip()
    return filename[:150]

def run_command(cmd, cwd=None):
    """Run a shell command and ensure it succeeds"""
    print(f"\n[*] Running: {' '.join(cmd)}")
    # Use ENV to ensure pathing or use full path if needed
    # Ensure PATH includes common locations for uv
    env = os.environ.copy()
    # Add common uv installation paths to PATH
    uv_paths = [
        os.path.expanduser("~/.local/bin"),
        os.path.expanduser("~/.cargo/bin"),
        "/usr/local/bin",
    ]
    for path in uv_paths:
        if path not in env.get('PATH', ''):
            env['PATH'] = f"{path}:{env.get('PATH', '')}"
    
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        print(f"[!] Warning: Command failed: {' '.join(cmd)}")
    return result.returncode == 0

def main(limit: int = 10):
    print("=== AI Economic Report Master Pipeline (v7.1) ===")
    
    # 0. Find uv executable (needed for NotebookLM operations)
    import shutil
    # Find uv in common locations
    UV_PATH = shutil.which("uv")
    if UV_PATH is None:
        # Try common installation paths
        common_paths = [
            os.path.expanduser("~/.local/bin/uv"),
            os.path.expanduser("~/.cargo/bin/uv"),
            "/usr/local/bin/uv",
        ]
        for path in common_paths:
            if os.path.exists(path):
                UV_PATH = path
                break
    
    if UV_PATH is None:
        print("[!] ERROR: 'uv' command not found. Please install uv or ensure it's in PATH.")
        print("    Installation: https://docs.astral.sh/uv/getting-started/installation/")
        sys.exit(1)
    
    print(f"[*] Using uv from: {UV_PATH}")
    
    # 1. Initialize NotebookLM Language (Ensure Japanese)
    # Using 'uv run' to ensure the virtual environment in the lab is used
    print("[*] Setting NotebookLM global language to 'ja' (Japanese)...")
    run_command([UV_PATH, "run", "python", "-m", "notebooklm", "language", "set", "ja"], cwd="notebooklm-podcast-lab")

    # Generate Date and Paths
    date_str = time.strftime("%Y%m%d")
    REPORTS_BASE = 'keizai-web/public/reports'
    REPORTS_SUBDIR = os.path.join(REPORTS_BASE, date_str)
    
    if not os.path.exists(REPORTS_SUBDIR):
        print(f"[*] Creating directory: {REPORTS_SUBDIR}")
        os.makedirs(REPORTS_SUBDIR)
    
    # 1. Start Scraper Phase (Fetch & Resolve)
    results = []
    with KeizaiScraper(headless=True) as scraper:
        RANKING_URL = "http://www3.keizaireport.com/ranking.php/-/node=2/"
        print(f"[*] Phase 1: Fetching ranking from {RANKING_URL}...")
        all_reports = scraper.get_ranking_reports(RANKING_URL)
        
        report_list = []
        for r in all_reports:
            title = r['title']
            # Removed filter for Ministry of Foreign Affairs reports
            # if "外務省" in title or "mofa" in r['jump_url'].lower():
            #     continue
            report_list.append(r)
            if len(report_list) >= limit:
                break
                
        print(f"[+] Processing top {len(report_list)} reports.")
        
        for i, entry in enumerate(report_list, 1):
            title = entry['title']
            jump_url = entry['jump_url']
            
            print(f"\n[*] Processing Rank {i}: {title}")
            final_url = scraper.resolve_jump_url(jump_url)
            
            if final_url:
                # 2. Save for NotebookLM ingestion
                # format: RankX_Title.md with Source: URL
                safe_title = sanitize_filename(title)
                filename = f"Rank{i}_{safe_title}.md"
                filepath = os.path.join(REPORTS_SUBDIR, filename)
                
                print(f"    - Saving report metadata for NotebookLM: {filename}")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# Rank {i}: {title}\n\n")
                    f.write(f"Source: {final_url}\n\n")
                    f.write(f"Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                results.append({"title": title, "url": final_url, "file": filepath})
                print(f"    [+] Saved successfully.")
            else:
                print(f"    [!] Failed to resolve URL for: {title}")
            
            time.sleep(1)

    # 3. Trigger Phase 2 & 3 if we have results
    if results:
        # Phase 2: NotebookLM Summarization (Native Briefing Doc)
        print("\n[*] Phase 2: Starting NotebookLM Summarization (Automation)...")
        run_command([UV_PATH, "run", "python", "generate_individual_notebooks.py"], cwd="notebooklm-podcast-lab")

        # Phase 3: Update Web Index (Syncing metadata and file paths)
        print("\n[*] Phase 3: Updating Web Index (reports.json)...")
        run_command(["python3", "build_index.py"])

        print(f"\n=== [🎉 SUCCESS] Daily Intelligence Pipeline Completed for {date_str} ===")
    else:
        print("[!] No reports were successfully processed.")

if __name__ == "__main__":
    import sys
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    main(limit=limit_arg)
