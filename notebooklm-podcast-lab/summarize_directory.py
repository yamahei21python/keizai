# summarize_directory.py
import os
import glob
import subprocess
import time
import re
import sys

# Configurations
UV_PATH = "/Users/kohei/.local/bin/uv"

def run_notebooklm(args):
    """Run notebooklm command using uv run"""
    cmd = [UV_PATH, "run", "python", "-m", "notebooklm"] + args
    print(f"[*] Executing: {' '.join(cmd)}")
    # Use check=True for critical failure, but here we capture to handle individually
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
    if len(sys.argv) < 2:
        print("Usage: python3 summarize_directory.py <target_directory_path>")
        sys.exit(1)

    target_dir = sys.argv[1]
    if not os.path.isdir(target_dir):
        print(f"[!] Error: {target_dir} is not a directory.")
        sys.exit(1)

    # Only target the source reports, not the generated summaries
    all_files = glob.glob(os.path.join(target_dir, "Rank*.md"))
    md_files = sorted([f for f in all_files if "Summary_Briefing" not in f])
    
    print(f"=== Starting Targeted Summarization for {len(md_files)} potential reports in {target_dir} ===")
    
    processing_queue = []

    for md_file in md_files:
        rank, title, urls = extract_metadata_and_urls(md_file)
        
        # Skip if summary already exists and is not empty
        output_md = os.path.join(target_dir, f"Rank{rank}_Summary_Briefing.md")
        if os.path.exists(output_md) and os.path.getsize(output_md) > 100:
            print(f"[*] Skipping Rank {rank}: Summary already exists.")
            continue

        notebook_name = f"[Targeted-Rank{rank}] {title[:40]}"
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
        
        processing_queue.append({
            "rank": rank,
            "id": notebook_id,
            "name": notebook_name,
            "output": output_md
        })

    if not processing_queue:
        print("\n[🎉 SUCCESS] No reports missing summaries in this directory.")
        return

    # Phase 2: Sequential Generation & Download
    print(f"\n=== Phase 2: Generating & Downloading {len(processing_queue)} missing summaries sequentially ===")
    for nb in processing_queue:
        print(f"\n>>> Processing: {nb['name']}...")
        run_notebooklm(["use", nb['id']])
        
        # 1. Generate (Wait)
        print(f"[*] Starting briefing-doc generation (waiting)...")
        gen_res = run_notebooklm(["generate", "report", "--format", "briefing-doc", "--wait"])
        if gen_res.returncode != 0:
            print(f"[!] Generation failed for {nb['name']}. Error: {gen_res.stderr}")
            continue

        # 2. Download
        print(f"[*] Harvesting report...")
        dl_res = run_notebooklm(["download", "report", nb['output']])
        
        if dl_res.returncode == 0:
            print(f"[🎉 SUCCESS] Summary saved: {nb['output']}")
            # Cleanup: Delete the notebook after successful download to keep workspace clean
            print(f"[*] Cleaning up: Deleting notebook {nb['id']}...")
            run_notebooklm(["delete", "--notebook", nb['id'], "--yes"])
        else:
            print(f"[!] Download failed for {nb['name']}. Error: {dl_res.stderr}")

    print("\n=== Targeted Summarization Task Completed ===")

if __name__ == "__main__":
    main()
