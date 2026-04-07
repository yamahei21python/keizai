# generate_individual_notebooks.py
import os
import glob
import subprocess
import time
import re

# Configurations
DATE_STR = time.strftime("%Y%m%d")
REPORTS_DIR = os.path.join("../keizai-web/public/reports", DATE_STR)
# Use date-based directory to avoid conflicts with existing reports
import shutil
UV_PATH = shutil.which("uv") or "uv"

def ensure_clean_directory(directory):
    """Remove existing directory and create fresh one"""
    if os.path.exists(directory):
        print(f"[*] Removing existing directory: {directory}")
        shutil.rmtree(directory)
    os.makedirs(directory, exist_ok=True)
        print(f"[+] Created fresh directory: {directory}")
import shutil
UV_PATH = shutil.which("uv") or "uv"

def run_notebooklm(args):
    """Run notebooklm command using uv run"""
    cmd = [UV_PATH, "run", "python", "-m", "notebooklm"] + args
    print(f"[*] Executing: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True)

def extract_metadata_and_urls(md_file):
    """Extract Rank, Title and ONLY relevant URLs (Source and PDF) from a markdown file"""
    filename = os.path.basename(md_file)
    match = re.match(r"Rank(\d+)_(.+)\.md", filename)
    rank = match.group(1) if match else "0"
    title_raw = match.group(2) if match else filename.replace(".md", "")
    
    urls = set()
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 1. Extract the Primary Source (from the 'Source:' line)
        source_match = re.search(r'^Source: (https?://\S+)', content, re.MULTILINE)
        if source_match:
            urls.add(source_match.group(1))
            
        # 2. Extract PDF links (any link containing .pdf)
        pdf_links = re.findall(r'https?://[^\s\)\>\]]+\.pdf[^\s\)\>\]]*', content, re.IGNORECASE)
        for pdf_url in pdf_links:
            urls.add(pdf_url.strip())
            
    return rank, title_raw, list(urls)

def main():
    # Only target the source reports, not the generated summaries
    all_files = glob.glob(os.path.join(REPORTS_DIR, "Rank*.md"))
    md_files = sorted([f for f in all_files if "Summary_Briefing" not in f])
    
    print(f"=== Starting Parallel Individual Notebook Generation for {len(md_files)} reports ===")
    
    notebook_queue = []

    # --- Phase 1: Ingestion (Create & Add Sources) ---
    for md_file in md_files:
        rank, title, urls = extract_metadata_and_urls(md_file)
        # Skip if report already exists and is not empty
        output_md = os.path.join(REPORTS_DIR, f"Rank{rank}_Summary_Briefing.md")
        if os.path.exists(output_md) and os.path.getsize(output_md) > 100:
            print(f"[*] Skipping Rank {rank}: Report already exists.")
            continue

        notebook_name = f"[Rank{rank}] {title[:40]}"
        print(f"\n>>> Preparing: {notebook_name}")
        
        # 1. Create Notebook
        res = run_notebooklm(["create", notebook_name])
        if res.returncode != 0:
            print(f"[!] Error creating notebook: {res.stderr}")
            continue
        
        try:
            notebook_id = res.stdout.split(":")[1].split("-")[0].strip()
            print(f"[+] Notebook created: {notebook_id}")
        except:
            print(f"[!] Could not parse notebook ID: {res.stdout}")
            continue

        # 2. Add Sources
        run_notebooklm(["use", notebook_id])
        for url in urls:
            print(f"[*] Adding source: {url}")
            run_notebooklm(["source", "add", url])
        
        notebook_queue.append({
            "rank": rank,
            "id": notebook_id,
            "name": notebook_name,
            "output": output_md
        })

    if not notebook_queue:
        print("\n[!] No notebooks to process.")
        return

    # --- Phase 2: Sequential Generation & Download ---
    print("\n=== Phase 2: Generating & Downloading finished reports ===")
    for i, nb in enumerate(notebook_queue, 1):
        print(f"\n>>> Processing: {nb['name']} ({i}/{len(notebook_queue)})...")
        run_notebooklm(["use", nb['id']])
        
        # 1. Generate with retry and polling
        print(f"[*] Starting briefing-doc generation...")
        gen_res = run_notebooklm(["generate", "report", "--format", "briefing-doc", "--retry", "5"])
        
        if gen_res.returncode != 0:
            error_msg = gen_res.stderr if gen_res.stderr else gen_res.stdout
            print(f"[!] Generation failed for {nb['name']}. Error: {error_msg}")
            continue
        
        # 2. Poll for report completion and download
        print(f"[*] Polling for report completion...")
        max_poll_attempts = 30  # 30 attempts = 10 minutes (20 seconds each)
        poll_interval = 20  # seconds
        
        for attempt in range(max_poll_attempts):
            print(f"    - Poll attempt {attempt + 1}/{max_poll_attempts}...")
            dl_res = run_notebooklm(["download", "report", nb['output']])
            
            if dl_res.returncode == 0:
                print(f"[🎉 SUCCESS] Report saved: {nb['output']}")
                # Cleanup: Delete the notebook after successful download to keep workspace clean
                print(f"[*] Cleaning up: Deleting notebook {nb['id']}...")
                run_notebooklm(["delete", "--notebook", nb['id'], "--yes"])
                break
            else:
                error_msg = dl_res.stderr if dl_res.stderr else dl_res.stdout
                if "No completed report artifacts found" in error_msg:
                    if attempt < max_poll_attempts - 1:
                        print(f"    - Report not ready yet, waiting {poll_interval} seconds...")
                        time.sleep(poll_interval)
                    else:
                        print(f"[!] Download failed for {nb['name']}. Report did not complete after {max_poll_attempts * poll_interval} seconds.")
                else:
                    print(f"[!] Download failed for {nb['name']}. Error: {error_msg}")
                    break
        
        # Rate limiting: Wait between reports to avoid API rate limits
        if i < len(notebook_queue):
            print(f"[*] Waiting 15 seconds before next report (rate limiting)...")
            time.sleep(15)

    print("\n=== All Tasks Completed ===")

if __name__ == "__main__":
    main()
