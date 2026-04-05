import os
import requests
from keizai_scraper import KeizaiScraper
import pytest

def test_actual_pdf_download():
    """
    スクレイパーで特定したPDFの直URLを使い、requestsで実際にダウンロードできるかテストする。
    """
    with KeizaiScraper(headless=True) as scraper:
        # ランキングからPDFレポートを探す
        ranking_url = "http://www3.keizaireport.com/ranking.php/-/node=2/"
        reports = scraper.get_ranking_reports(ranking_url)
        
        pdf_url = None
        for report in reports[:5]:
            final_url = scraper.resolve_jump_url(report['jump_url'])
            if final_url.lower().endswith('.pdf'):
                pdf_url = final_url
                break
        
        if not pdf_url:
            pytest.skip("No PDF report found in top 5 to test download.")

        print(f"[*] Attempting to download PDF: {pdf_url}")
        
        # unified_pipeline.py の download_pdf ロジックに近い形で実行
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Referer': 'http://www3.keizaireport.com/'
        }
        
        response = requests.get(pdf_url, headers=headers, timeout=30)
        assert response.status_code == 200
        assert len(response.content) > 1000 # 1KB以上はあるはず
        
        # 一時ファイルとして保存
        test_file = "test_download.pdf"
        with open(test_file, "wb") as f:
            f.write(response.content)
        
        print(f"[+] Successfully downloaded {len(response.content)} bytes to {test_file}")
        
        # クリーンアップ
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    pytest.main([__file__, "-s"])
