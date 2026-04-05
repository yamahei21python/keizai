-- resolve_jump.scpt
-- Usage: osascript resolve_jump.scpt "/jump.php?RID=..."

on run argv
    set partialURL to item 1 of argv
    set baseURL to "http://www3.keizaireport.com"
    set fullURL to baseURL & partialURL
    
    tell application "Google Chrome"
        activate
        -- Reuse current tab unless it's the ranking page
        tell window 1
            set currentURL to URL of active tab
            if currentURL contains "ranking.php" or currentURL contains "keizaireport.com/index.php" then
                make new tab with properties {URL: fullURL}
            else
                set URL of active tab to fullURL
            end if
        end tell
        
        -- Wait for the redirect to settle (usually fast, but let's give it 5-8s)
        delay 8
        
        -- Get the final URL
        set finalURL to URL of active tab of window 1
        return finalURL
    end tell
end run
