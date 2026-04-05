from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time

def test_direct_link():
    with sync_playwright() as p:
        # ヘッドレスモードで実行
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        stealth_sync(page)

        # 1. ランキングページからリンクを取得
        ranking_url = "http://www3.keizaireport.com/ranking.php/-/node=2/"
        print(f"[*] ランキングページに移動中: {ranking_url}")
        page.goto(ranking_url)
        page.wait_for_selector('a[href*="jump.php"]')
        
        # 最初のジャンプリンクを取得
        jump_link_el = page.query_selector('a[href*="jump.php"]')
        href = jump_link_el.get_attribute('href')
        full_jump_url = f"http://www3.keizaireport.com{href}" if href.startswith('/') else href
        print(f"[*] 取得したジャンプURL: {full_jump_url}")

        # 2. ジャンプURLに移動してリダイレクトを監視
        print("[*] ジャンプURLに移動し、最終的なリダイレクト先を確認します...")
        
        try:
            # ページ移動
            page.goto(full_jump_url, wait_until="load", timeout=30000)
            
            # メタフレッシュやJSリダイレクトのために10秒待機
            print("[*] リダイレクト待機中 (10秒)...")
            for i in range(10):
                time.sleep(1)
                # 1秒ごとにURLが変化したかログに出す
                print(f"    {i+1}秒後のURL: {page.url}")
            
            print("\n--- 検証結果 ---")
            print(f"最終URL: {page.url}")
            print(f"ページタイトル: {page.title()}")
            
            # PDFが埋め込み表示されている場合、iframeなどで別URLが動いている可能性があるため確認
            iframes = page.frames
            if len(iframes) > 1:
                print(f"検出されたフレーム数: {len(iframes)}")
                for i, frame in enumerate(iframes):
                    print(f"  Frame {i} URL: {frame.url}")

        except Exception as e:
            print(f"[!] エラーが発生しました: {e}")
        
        browser.close()

if __name__ == "__main__":
    test_direct_link()
