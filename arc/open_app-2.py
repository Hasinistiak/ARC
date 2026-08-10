import os
import difflib

apps = {
    "chrome": "chrome.exe",
    "spotify": "C:\\Users\\ENAN\\AppData\\Roaming\\Spotify\\Spotify.exe",
    "files": "explorer.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "blip": "blip.exe",
    "code": "code",
    "chatgpt": "chatgpt.exe",
    "calendar": "C:\\Users\\ENAN\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Chrome Apps\\Google Calendar.lnk",
    "settings": "ms-settings:",
    "whatsapp": "WhatsApp.exe",
    "windhawk": "C:\\Program Files\\Windhawk\\windhawk.exe",
    "cmd": "cmd.exe",
}

def find_best_match(user_input, choices):
    matches = difflib.get_close_matches(user_input, choices, n=1, cutoff=0.5)
    return matches[0] if matches else None

def open_app(app_name):
    app_name = app_name.lower().strip()

    # direct match first
    if app_name in apps:
        target = app_name
    else:
        # fuzzy match fallback
        match = find_best_match(app_name, apps.keys())
        if match:
            target = match
        else:
            print(f"ARC: Unknown app: {app_name}")
            return

    try:
        os.startfile(apps[target])
        print(f"ARC: Opening {target}...")
    except FileNotFoundError:
        print(f"ARC: {apps[target]} not found.")
