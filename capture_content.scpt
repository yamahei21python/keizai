-- capture_content.scpt
-- Usage: osascript capture_content.scpt "https://example.com"

on run argv
    set targetURL to item 1 of argv
    
    tell application "Google Chrome"
        activate
        -- Check if the active tab is already at the target URL to avoid duplicates
        tell window 1
            if URL of active tab is not targetURL then
                set URL of active tab to targetURL
            end if
        end tell
        
        -- Wait for the content to render (PwC/METI/MOFA)
        delay 15
        
        try
            -- Attempt 1: Get innerText AND all link URLs via JavaScript
            set jsCode to "
                let text = document.body.innerText;
                let links = Array.from(document.querySelectorAll('a[href]')).map(a => a.href).filter(h => h.startsWith('http')).join('\\n');
                '--- CONTENT ---\\n' + text + '\\n\\n--- LINKS ---\\n' + links
            "
            set renderedPageText to execute active tab of window 1 javascript jsCode
            
            return renderedPageText
            
        on error
            -- Attempt 2: Last Resort GUI Capture (Command+A, Command+C)
            tell application "System Events"
                tell process "Google Chrome"
                    set frontmost to true
                    -- Click in the center to focus the document/PDF
                    click at {500, 500}
                    delay 0.5
                    -- Command+A (Select All)
                    keystroke "a" using command down
                    delay 0.5
                    -- Command+C (Copy)
                    keystroke "c" using command down
                    delay 1.0
                end tell
            end tell
            
            -- Get content from clipboard
            set clipboardText to the clipboard
            return clipboardText
        end try
    end tell
end run
