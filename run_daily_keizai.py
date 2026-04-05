# run_daily_keizai.py
import os
import subprocess
import time
import glob
import sys

# Configuration
DATE_STR = time.strftime("%Y%m%d")
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "keizai-web/public/reports", DATE_STR)

def run_command(cmd, cwd=None):
    """Run a shell command and ensure it succeeds"""
    print(f"\n[*] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"[!] Command failed: {' '.join(cmd)}")
        sys.exit(1)

def check_and_start_browser():
    """Ensure Google Chrome is running on macOS"""
    print("[*] Checking for browser status...")
    # 'pgrep' checks if the process is running
    status = subprocess.run(["pgrep", "-x", "Google Chrome"], capture_output=True)
    if status.returncode != 0:
        print("[!] Google Chrome is not running. Launching now...")
        subprocess.run(["open", "-a", "Google Chrome"])
        # Give it a few seconds to initialize
        time.sleep(5)
    else:
        print("[+] Google Chrome is already active.")

def main():
    print(f"=== Daily Keizai Intelligence Pipeline: {DATE_STR} ===")
    
    # 1. Skip logic: Check if any summary briefing exists in today's folder
    summaries = []
    if os.path.exists(REPORTS_DIR):
        summaries = glob.glob(os.path.join(REPORTS_DIR, "Rank*_Summary_Briefing.md"))

    if summaries:
        print(f"[*] Found {len(summaries)} existing summaries. Skipping Phase 1 (Report Fetching).")
    else:
        print("[*] No summaries found or folder is empty. Starting Phase 1: Report Fetching...")
        # Step 0: Ensure browser is open
        check_and_start_browser()
        
        # Step 1: unified_pipeline.py
        # Note: This requires Chrome to be open on the correct page
        run_command(["python3", "unified_pipeline.py"])

    # Phase 2: Individual Summarization (NotebookLM)
    # This script automatically skips reports that already have summaries
    print("\n[*] Starting Phase 2: NotebookLM Individual Summarization...")
    # Run from the notebooklm-podcast-lab directory to maintain its internal pathing
    run_command(["python3", "generate_individual_notebooks.py"], cwd="notebooklm-podcast-lab")

    # Phase 3: Update Web Index
    print("\n[*] Starting Phase 3: Updating Web Index...")
    run_command(["python3", "build_index.py"])

    print(f"\n=== [🎉 SUCCESS] Daily Pipeline Completed for {DATE_STR} ===")

if __name__ == "__main__":
    main()
