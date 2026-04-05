import os
import json
import re
import glob

def extract_meta_from_md(file_path):
    """Extract Title and Source URL from the original source markdown."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Title is usually the first line (e.g., # Rank 1: Title)
    title_match = re.search(r'^# Rank \d+: (.+)', content, re.MULTILINE)
    title = title_match.group(1) if title_match else os.path.basename(file_path)
    
    # Source URL
    source_match = re.search(r'^Source: (https?://\S+)', content, re.MULTILINE)
    source_url = source_match.group(1) if source_match else ""
    
    return title, source_url

def build_index():
    reports_root = "keizai-web/public/reports"
    dates = sorted([d for d in os.listdir(reports_root) if os.path.isdir(os.path.join(reports_root, d))], reverse=True)
    
    all_reports = []
    
    for date_str in dates:
        date_dir = os.path.join(reports_root, date_str)
        # Find all source files (those without 'Summary_Briefing')
        source_files = glob.glob(os.path.join(date_dir, "Rank[0-9]*_*.md"))
        source_files = [f for f in source_files if "Summary_Briefing" not in f]
        
        for sf in source_files:
            filename = os.path.basename(sf)
            rank_match = re.match(r"Rank(\d+)_", filename)
            if not rank_match:
                continue
            rank = int(rank_match.group(1))
            
            title, source_url = extract_meta_from_md(sf)
            
            # Look for matching summary
            summary_pattern = os.path.join(date_dir, f"Rank{rank}_Summary_Briefing.md")
            has_summary = os.path.exists(summary_pattern)
            
            all_reports.append({
                "date": date_str,
                "rank": rank,
                "title": title,
                "source_url": source_url,
                "source_file": sf,
                "summary_file": summary_pattern if has_summary else None,
                "status": "completed" if has_summary else "processing"
            })
            
    # Sort by date desc, then rank asc
    all_reports.sort(key=lambda x: (x['date'], -x['rank']), reverse=True)
    
    index_data = {
        "dates": dates,
        "reports": all_reports
    }
    
    # Ensure directory for JSON
    os.makedirs("keizai-web/src/data", exist_ok=True)
    with open("keizai-web/src/data/reports.json", "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
        
    print(f"[+] Index built successfully with {len(all_reports)} reports.")

if __name__ == "__main__":
    build_index()
