# cleanup_notebooks.py
import json
import subprocess
import os

# Configurations
UV_PATH = "/Users/kohei/.local/bin/uv"

def run_notebooklm(args):
    """Run notebooklm command using uv run"""
    cmd = [UV_PATH, "run", "python", "-m", "notebooklm"] + args
    print(f"[*] Executing: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True)

def main():
    print("=== NotebookLM Workspace Cleanup ===")
    
    # 1. List all notebooks in JSON format
    print("[*] Fetching notebook list...")
    res = run_notebooklm(["list", "--json"])
    if res.returncode != 0:
        print(f"[!] Error listing notebooks: {res.stderr}")
        return

    try:
        data = json.loads(res.stdout)
        notebooks = data.get("notebooks", [])
    except json.JSONDecodeError:
        print(f"[!] Error parsing JSON output: {res.stdout}")
        return

    # 2. Filter notebooks
    # Pattern: Starts with [Rank or [Targeted-Rank
    to_delete = []
    for nb in notebooks:
        title = nb.get("title", "")
        # The user said anything with [Rank is related
        if title.startswith("[Rank") or title.startswith("[Targeted-Rank"):
            to_delete.append(nb)

    if not to_delete:
        print("[🎉 SUCCESS] No project-related notebooks found to delete.")
        return

    print(f"[+] Found {len(to_delete)} notebooks to delete:")
    for nb in to_delete:
        print(f"  - {nb['title']} (ID: {nb['id']})")

    # 3. Delete each notebook
    for nb in to_delete:
        print(f"\n[*] Deleting: {nb['title']}...")
        del_res = run_notebooklm(["delete", "--notebook", nb['id'], "--yes"])
        if del_res.returncode == 0:
            print(f"[🎉 SUCCESS] Deleted: {nb['id']}")
        else:
            print(f"[!] Delete failed for {nb['id']}. Error: {del_res.stderr}")

    print("\n=== Cleanup Completed ===")

if __name__ == "__main__":
    main()
