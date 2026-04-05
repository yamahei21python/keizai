from keizai_scraper import KeizaiScraper
import pytest

# 調査で見つかった具体的なテスト用RID
RID_DIRECT_PDF = "617420"  # 浜銀総合研究所 (直接PDF)
RID_DEEP_DISCOVERY = "661646" # 伊藤忠総研 (紹介ページ経由PDF)
RID_HTML_ONLY = "662136" # 野村総合研究所 (HTMLコラム)

@pytest.fixture(scope="module")
def scraper():
    with KeizaiScraper(headless=True) as s:
        yield s

def test_resolve_direct_pdf(scraper):
    """ケース1: 直接PDFにリダイレクトされる場合"""
    jump_url = f"http://www3.keizaireport.com/jump.php?RID={RID_DIRECT_PDF}"
    final_url = scraper.resolve_jump_url(jump_url)
    
    print(f"\n[Direct PDF Test] {final_url}")
    assert final_url.lower().endswith('.pdf')
    assert "keizaireport.com" not in final_url # 外部サイトのURLになっていること

def test_resolve_deep_discovery_pdf(scraper):
    """ケース2: HTML紹介ページから内部のPDFを見つけ出す場合"""
    jump_url = f"http://www3.keizaireport.com/jump.php?RID={RID_DEEP_DISCOVERY}"
    final_url = scraper.resolve_jump_url(jump_url)
    
    print(f"\n[Deep Discovery Test] {final_url}")
    # 到着先がHTMLであっても、その中のPDFを拾えているか
    assert final_url.lower().endswith('.pdf')
    assert "itochu-research.com" in final_url

def test_resolve_html_only(scraper):
    """ケース3: PDFが存在しないHTML単体のページの場合"""
    jump_url = f"http://www3.keizaireport.com/jump.php?RID={RID_HTML_ONLY}"
    final_url = scraper.resolve_jump_url(jump_url)
    
    print(f"\n[HTML Only Test] {final_url}")
    # PDFがない場合は、元のサイトURL（HTML）を返しているか
    assert not final_url.lower().endswith('.pdf')
    assert "nri.co.jp" in final_url

if __name__ == "__main__":
    pytest.main([__file__, "-s"])
