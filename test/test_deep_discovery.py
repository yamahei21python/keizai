from keizai_scraper import KeizaiScraper
import pytest

TARGET_URL = "http://www3.keizaireport.com/ranking.php/-/node=2/"

@pytest.fixture(scope="module")
def scraper():
    with KeizaiScraper(headless=True) as s:
        yield s

def test_dynamic_deep_discovery(scraper):
    """最新のランキングから動的にレポートを取得し、PDFまで解決できるかテストする"""
    print(f"\n[*] Fetching latest ranking from: {TARGET_URL}")
    reports = scraper.get_ranking_reports(TARGET_URL)
    
    assert len(reports) > 0, "ランキングが空です。WAFでブロックされている可能性があります。"
    print(f"[+] Found {len(reports)} reports. Testing first 6...")

    for i, report in enumerate(reports[:6]):
        print(f"\n--- Testing Report {i+1}: {report['title']} ---")
        jump_url = report['jump_url']
        
        # 解決実行 (refererとしてランキングURLを渡す)
        final_url = scraper.resolve_jump_url(jump_url, referer=TARGET_URL)
        
        assert final_url is not None
        assert final_url.startswith('http')
        assert "keizaireport.com/jump.php" not in final_url, "Jump URLが解決されていません"
        
        print(f"[+] Resolved to: {final_url}")
        
        # PDFかどうかの判定（任意だがログ出力）
        if final_url.lower().endswith('.pdf'):
            print("[*] Result is a PDF.")
        else:
            print("[*] Result is an HTML page.")

if __name__ == "__main__":
    pytest.main([__file__, "-s"])
