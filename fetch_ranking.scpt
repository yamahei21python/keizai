-- fetch_ranking.scpt
-- Robust script to open the ranking page and extract accessible 'Direct Jump' reports.

on run
    set targetURL to "http://www3.keizaireport.com/ranking.php/-/node=2/"
    
    tell application "Google Chrome"
        activate
        -- Open the URL in a new tab
        if (count of windows) is 0 then
            make new window with properties {tab: {URL: targetURL}}
        else
            tell window 1 to make new tab with properties {URL: targetURL}
        end if
        
        -- EXTENDED DELAY to ensure the ranking list is fully rendered
        delay 20
        
        -- Execute JS
        set results to execute active tab of window 1 javascript "
        (function() {
            let reports = [];
            let jumpLinks = document.querySelectorAll('a[href*=\"jump.php\"]');
            
            if (jumpLinks.length === 0) return '';
            
            jumpLinks.forEach(link => {
                let href = link.getAttribute('href');
                let container = link.closest('div') || link.parentElement;
                let fullText = container.innerText;
                
                if (!fullText.includes('会員専用')) {
                    let ridMatch = href.match(/RID=(\\d+)/);
                    if (ridMatch) {
                        let rid = ridMatch[1];
                        let titleLink = document.querySelector('a.r_t[href*=\"/' + rid + '/\"]');
                        if (titleLink) {
                            let title = titleLink.innerText.trim();
                            if (!reports.some(r => r.startsWith(title + '|'))) {
                                reports.push(title + '|' + href);
                            }
                        }
                    }
                }
            });
            return reports.join('\\n');
        })()
        "
        return results
    end tell
end run
