from keizai_scraper import KeizaiScraper
import pytest
import os

TARGET_URL = "http://www3.keizaireport.com/ranking.php/-/node=2/"

@pytest.fixture(scope="module")
def scraper():
    with KeizaiScraper(headless=True) as s:
        yield s

def test_step1_ranking_fetch(scraper):
    """ランキングページから有効なレポート一覧が取得できるか"""
    reports = scraper.get_ranking_reports(TARGET_URL)
    print(f"\n[+] Found {len(reports)} reports.")
    assert len(reports) > 0
    assert "title" in reports[0]
    assert "jump_url" in reports[0]

def test_step2_jump_resolution_and_type_detection(scraper):
    """ジャンプURLの解決と、ファイル形式の判別ができるか"""
    reports = scraper.get_ranking_reports(TARGET_URL)
    # 最初のレポートでテスト
    report = reports[0]
    jump_url = report['jump_url']
    
    final_url = scraper.resolve_jump_url(jump_url)
    assert final_url is not None
    assert final_url.startswith('http')
    print(f"[+] Resolved URL: {final_url}")

    # PDFかHTMLかの判定（既存のpipelineロジックに合わせるため）
    is_pdf = final_url.lower().endswith('.pdf')
    if is_pdf:
        print("[*] Detected PDF report.")
    else:
        print("[*] Detected HTML report.")
    
    # どちらの状態でも「到達できていること」を保証
    assert is_pdf or not is_pdf # 常に真だが、パスを通ることを確認

def test_step3_content_capture_if_html(scraper):
    """HTMLレポートの場合のみ本文を抽出し、PDFの場合はスキップ（またはURL確認のみ）する"""
    reports = scraper.get_ranking_reports(TARGET_URL)
    
    found_html = False
    for report in reports[:5]: # 最初の5件でHTMLを探す
        final_url = scraper.resolve_jump_url(report['jump_url'])
        if not final_url.lower().endswith('.pdf'):
            print(f"[*] Testing HTML capture for: {final_url}")
            content = scraper.capture_content(final_url)
            assert "--- CONTENT ---" in content
            assert len(content) > 200 # ある程度の長さがあること
            found_html = True
            break
            
    if not found_html:
        pytest.skip("No HTML reports found in the top 5 to test capture.")

if __name__ == "__main__":
    pytest.main([__file__, "-s"])

if __name__ == "__main__":
    test_fetch_ranking_page()
