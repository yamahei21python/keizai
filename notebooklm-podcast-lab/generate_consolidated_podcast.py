# generate_consolidated_podcast.py
import os
import glob
import subprocess
import time

# Configurations
REPORTS_DIR = "../reports"
UV_PATH = "/Users/kohei/.local/bin/uv"
NOTEBOOK_NAME = f"Economic_Intelligence_{time.strftime('%Y%m%d')}"
OUTPUT_MP3 = "../reports/Daily_Full_Consolidated_Podcast.mp3"

def run_notebooklm(args):
    """Run notebooklm command using uv run"""
    cmd = [UV_PATH, "run", "notebooklm"] + args
    print(f"[*] Executing: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True)

def extract_urls_from_markdowns():
    """Scan markdowns in reports/ and extract Source URLs AND any direct PDF links inside"""
    urls = []
    md_files = glob.glob(os.path.join(REPORTS_DIR, "Rank*.md"))
    print(f"[*] Scanning {len(md_files)} markdown files for URLs and nested PDFs...")
    
    for md_file in md_files:
        with open(md_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 1. Base Source URL
                if line.startswith("Source:"):
                    url = line.replace("Source:", "").strip()
                    if url.startswith("http"):
                        urls.append(url)
                
                # 2. Look for explicit PDF links in the body (e.g. [title](url.pdf))
                if ".pdf" in line.lower() and "http" in line:
                    import re
                    # Simple regex to find http...pdf
                    found_pdf = re.findall(r'https?://[^\s\)\>\]]+\.pdf', line, re.IGNORECASE)
                    for pdf_url in found_pdf:
                        # Filter out some generic ones if needed, but mostly add them
                        if "mofa.go.jp" in pdf_url or "marubeni.com" in pdf_url or "meti.go.jp" in pdf_url:
                            urls.append(pdf_url)
                        else:
                            urls.append(pdf_url)
    
    # Clean up and unique
    unique_urls = list(set([u.strip() for u in urls if u.strip().startswith("http")]))
    return unique_urls

def main():
    print(f"=== NotebookLM Consolidated Podcast Generator ===")

    # 1. Extract URLs
    urls = extract_urls_from_markdowns()
    if not urls:
        print("[!] No URLs found in reports folder. Please run unified_pipeline.py first.")
        return

    print(f"[+] Found {len(urls)} reports to consolidate.")

    # 2. Create Notebook
    print(f"[*] Creating notebook: {NOTEBOOK_NAME}")
    res = run_notebooklm(["create", NOTEBOOK_NAME])
    if res.returncode != 0:
        print(f"[!] Error creating notebook: {res.stderr}")
        return
    
    # Extract ID from "Created notebook: <ID> - <Name>"
    try:
        notebook_id = res.stdout.split(":")[1].split("-")[0].strip()
        print(f"[+] Notebook created: {notebook_id}")
    except:
        print(f"[!] Could not parse notebook ID from output: {res.stdout}")
        return

    # 3. Use Notebook
    run_notebooklm(["use", notebook_id])

    # 4. Add Sources (Bulk)
    for url in urls:
        print(f"[*] Adding source: {url}")
        run_notebooklm(["source", "add", url])
    
    print("[*] Waiting for sources to process (30s)...")
    time.sleep(30)

    # 5. Generate Consolidated Podcast (Multi-source analysis)
    # Custom analytic prompt provided by the user
    prompt = """
これらすべての経済レポートを統合し、今日の世界経済で起きていることの全容、共通の潮流、および各セクターの重要なリスクを、投資家が聴くべき要約ポッドキャストとして日本語で詳しく解説してください。
"""
    
    print(f"[*] Generating consolidated audio overview with analyst prompt...")
    # --wait flag to block until generation is complete (usually 5-10 mins)
    gen_res = run_notebooklm(["generate", "audio", prompt, "--wait"])
    
    if gen_res.returncode != 0:
        print(f"[!] Audio generation encountered an issue or timed out (background process might still be running).")
        print(f"Details: {gen_res.stderr}")
        # Even if it times out, we can try downloading if the process finished on Google server.
    
    # 6. Download
    print(f"[*] Attempting to download the consolidated podcast to: {OUTPUT_MP3}")
    dl_res = run_notebooklm(["download", "audio", OUTPUT_MP3])
    
    if dl_res.returncode == 0:
        print(f"\n[🎉 SUCCESS] Consolidated podcast saved to: {OUTPUT_MP3}")
    else:
        print(f"[!] Download failed. You may need to wait a few more minutes and run 'uv run notebooklm download audio {OUTPUT_MP3}' manually.")
        print(f"Error: {dl_res.stderr}")

if __name__ == "__main__":
    main()
