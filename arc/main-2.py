import os
import subprocess
import sys
from music import play_song
from open_app import open_app, apps
from open_site import open_site
from search import google_search
from file_search import search_everything_gui
import tkinter as tk
import threading


modes = {
    "dev": ["spotify", "code", "chatgpt"],
    "social": ["site yt", "site ig", "site threads", "site facebook"]
}

def run_mode(mode_name):
    mode_name = mode_name.lower().strip()

    if mode_name not in modes:
        print(f"\nARC: Mode '{mode_name}' not found\n")
        return False

    print(f"\nARC: Activating {mode_name.upper()} mode...\n")

    for action in modes[mode_name]:
        handle_command(action)

    spacer()
    return False

def boot_screen():
    print("\n" + "═" * 45)
    print("   ARC MARK - 2.0")
    print("═" * 45 + "\n")

def spacer():
    print("\n" + "-" * 45 + "\n")

def new_project(_):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, "AutoProjectCreation.py")
    
    subprocess.run([sys.executable, script_path])

def system_control(action):
    action = action.strip().lower()

    if action == "shutdown":
        print("\nARC: Shutting down system...\n")
        os.system("shutdown /s /t 0")

    elif action == "restart":
        print("\nARC: Restarting system...\n")
        os.system("shutdown /r /t 0")

    elif action == "lock":
        print("\nARC: Locking system...\n")
        os.system("rundll32.exe user32.dll,LockWorkStation")

commands = {
    "open": {
        "func": open_app,
        "desc": "Open an application → chrome"
    },
    "new project": {
        "func": new_project,
        "desc": "Create New Project → project"
    },
    "exit": {
        "func": None,
        "desc": "Exit program"
    },
    "system": {
        "func": system_control,
        "desc": "System control → shutdown / restart / sleep"
    },
    "file": {
        "func": search_everything_gui,
        "desc": "Search files with Everything Search → file [query]"
    },
    "play": {
        "func": play_song,
        "desc": "Play a song on Spotify → play [song name]"
    }


}

def handle_multi_input(user_input):
    parts = [p.strip() for p in user_input.split(",")]

    for part in parts:
        handle_command(part)

    spacer()

def handle_command(user_input):
    user_input = " ".join(user_input.strip().lower().split())  
    

    for cmd in commands:
        if user_input.startswith(cmd):
            arg = user_input[len(cmd):].strip()

            if cmd == "exit":
                print("\nARC: Shutting down system...\n")
                return False

            commands[cmd]["func"](arg)
            return False

    # fallback commands
    if user_input.startswith("site "):
        open_site(user_input[5:])
        return False
    
    elif user_input in modes:
        run_mode(user_input)
        return False

    elif user_input.startswith("search "):
        google_search(user_input[7:])
        return False

    elif user_input.startswith("play "):
        play_song(user_input[5:])
        return False

    elif user_input.startswith("file "):
        search_everything_gui(user_input[5:])
        return False

    else:
        open_app(user_input)
        return False

boot_screen()

class ArcLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ARC Launcher")

        width = 600
        height = 60

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2

        y = (screen_height - height) // 2 - 150

        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.root.configure(bg="#070707")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self.entry = tk.Entry(
            self.root,
            font=("Consolas", 18),
            bg="#070707",
            fg="white",
            insertbackground="white",
            relief="flat"
        )
        self.entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<Escape>", lambda e: self.root.destroy())

        self.entry.focus()

    def on_enter(self, event=None):
        user_input = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        if "," in user_input:
            handle_multi_input(user_input)
        else:
            should_exit = handle_command(user_input)
            if should_exit is False:
                self.root.destroy()

    def run(self):
        self.root.mainloop()


def start_arc_ui():
    app = ArcLauncher()
    app.run()


if __name__ == "__main__":
    start_arc_ui()