import os
import pymupdf4llm
import requests
from keizai_scraper import KeizaiScraper
import pytest

def test_pdf_parsing_to_markdown():
    """
    ダウンロードしたPDFを PyMuPDF4LLM で正しく Markdown に変換できるか検証する。
    """
    with KeizaiScraper(headless=True) as scraper:
        # 1. テスト用のPDFを1つ取得
        ranking_url = "http://www3.keizaireport.com/ranking.php/-/node=2/"
        reports = scraper.get_ranking_reports(ranking_url)
        
        pdf_url = None
        for report in reports[:5]:
            final_url = scraper.resolve_jump_url(report['jump_url'])
            if final_url.lower().endswith('.pdf'):
                pdf_url = final_url
                break
        
        if not pdf_url:
            pytest.skip("No PDF report found in top 5 to test parsing.")

        # 2. ダウンロード
        print(f"[*] Downloading PDF for parsing test: {pdf_url}")
        response = requests.get(pdf_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        
        temp_pdf = "temp_test_parse.pdf"
        with open(temp_pdf, "wb") as f:
            f.write(response.content)
        
        try:
            # 3. PyMuPDF4LLM で変換
            print("[*] Parsing PDF with PyMuPDF4LLM...")
            content = pymupdf4llm.to_markdown(temp_pdf)
            
            # 結果の検証
            assert content is not None
            assert len(content) > 500 # 最低限のボリューム
            print(f"[+] Successfully parsed PDF! Length: {len(content)} chars.")
            # print(content[:500]) # 冒頭を表示
            
        finally:
            # クリーンアップ
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)

if __name__ == "__main__":
    pytest.main([__file__, "-s"])
