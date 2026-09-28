from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import tkinter as tk
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from open_app import open_app
from open_site import open_site
from search import google_search
from file_search import search_everything_gui


# ============================================================================
# CONFIGURATION
# ============================================================================

APP_NAME = "ARC"
VERSION = "3.0"

WINDOW_WIDTH = 720
WINDOW_HEIGHT = 190
WINDOW_OFFSET_Y = 150

# Stark monochrome palette
BG_COLOR = "#050505"
PANEL_COLOR = "#0A0A0A"
INPUT_COLOR = "#0D0D0D"
BORDER_COLOR = "#242424"
BORDER_ACTIVE = "#5A5A5A"
FG_COLOR = "#F5F5F5"
MUTED_COLOR = "#777777"
DIM_COLOR = "#454545"
ACCENT_COLOR = "#F2F2F2"
ERROR_COLOR = "#FF4D4D"

FONT_MAIN = ("Consolas", 18)
FONT_COMMAND = ("Consolas", 18, "bold")
FONT_SMALL = ("Consolas", 9)
FONT_LABEL = ("Consolas", 10, "bold")
FONT_HINT = ("Consolas", 10)

ZOE_SERVER_URL = "http://127.0.0.1:8000"
ZOE_CHAT_URL = f"{ZOE_SERVER_URL}/api/chat"


# ============================================================================
# COMMAND VISUALS
# ============================================================================

COMMAND_META = {
    "open": {
        "label": "OPEN",
        "description": "Open an application",
    },
    "site": {
        "label": "SITE",
        "description": "Open a website",
    },
    "search": {
        "label": "SEARCH",
        "description": "Search the web",
    },
    "file": {
        "label": "FILE",
        "description": "Search files",
    },
    "new project": {
        "label": "PROJECT",
        "description": "Create a new project",
    },
    "system": {
        "label": "SYSTEM",
        "description": "System control",
    },
    "exit": {
        "label": "EXIT",
        "description": "Close ARC",
    },
    "zoe": {
        "label": "ZOE",
        "description": "Send command to ZOE",
    },
}


# ============================================================================
# MODES
# ============================================================================

MODES = {
    "dev": [
        "open spotify",
        "open code",
        "open chatgpt",
    ],
    "social": [
        "site yt",
        "site ig",
        "site threads",
        "site facebook",
    ],
}


# ============================================================================
# COMMAND MODEL
# ============================================================================

@dataclass
class Command:
    name: str
    handler: Callable[[str], None]
    description: str
    aliases: tuple[str, ...] = ()


# ============================================================================
# ARC CORE
# ============================================================================

class ArcCore:

    def __init__(
        self,
        ui_callback: Callable[[str, str], None] | None = None,
        zoe_response_callback: Callable[[str, str], None] | None = None,
    ):
        self.running = True
        self.commands: list[Command] = []
        self.ui_callback = ui_callback
        self.zoe_response_callback = zoe_response_callback

        self._register_commands()

    # ------------------------------------------------------------------------
    # UI COMMUNICATION
    # ------------------------------------------------------------------------

    def status(
        self,
        message: str,
        kind: str = "normal",
    ):
        print(f"ARC: {message}")

        if self.ui_callback:
            self.ui_callback(message, kind)

    # ------------------------------------------------------------------------
    # COMMAND REGISTRATION
    # ------------------------------------------------------------------------

    def _register_commands(self):

        self.commands = [
            Command(
                name="open",
                handler=self.command_open,
                description="Open an application → open chrome",
            ),
            Command(
                name="site",
                handler=self.command_site,
                description="Open a website → site yt",
            ),
            Command(
                name="search",
                handler=self.command_search,
                description="Google search → search something",
            ),
            Command(
                name="file",
                handler=self.command_file,
                description="Search files → file query",
            ),
            Command(
                name="new project",
                handler=self.command_new_project,
                description="Create a new project",
            ),
            Command(
                name="system",
                handler=self.command_system,
                description="System control → shutdown / restart / lock",
            ),
            Command(
                name="exit",
                handler=self.command_exit,
                description="Exit ARC",
                aliases=("quit", "q"),
            ),
        ]

    # ------------------------------------------------------------------------
    # INPUT NORMALIZATION
    # ------------------------------------------------------------------------

    @staticmethod
    def normalize(text: str) -> str:
        return " ".join(text.strip().lower().split())

    # ------------------------------------------------------------------------
    # MAIN ROUTER
    # ------------------------------------------------------------------------

    def handle(self, user_input: str) -> bool:

        user_input = self.normalize(user_input)

        if not user_input:
            return True

        # --------------------------------------------------------------------
        # ZOE ROUTING
        # --------------------------------------------------------------------

        if user_input == "zoe" or user_input.startswith("zoe "):
            self.command_zoe(user_input[3:].strip())

            # Keep ARC open for ZOE.
            return True

        # --------------------------------------------------------------------
        # MODES
        # --------------------------------------------------------------------

        if user_input in MODES:
            self.run_mode(user_input)

            # Non-ZOE commands close ARC.
            return False

        # --------------------------------------------------------------------
        # REGISTERED COMMANDS
        # --------------------------------------------------------------------

        for command in self.commands:

            names = (
                command.name,
                *command.aliases,
            )

            for name in names:

                if user_input == name:
                    argument = ""

                elif user_input.startswith(name + " "):
                    argument = user_input[len(name):].strip()

                else:
                    continue

                try:
                    command.handler(argument)

                except Exception as exc:
                    self.report_error(
                        command.name,
                        exc,
                    )

                # Exit is handled specially.
                if command.name == "exit":
                    return self.running

                # Every non-ZOE command closes ARC.
                return False

        # --------------------------------------------------------------------
        # CONVENIENCE:
        #
        # Typing "chrome" still opens Chrome.
        # --------------------------------------------------------------------

        try:
            open_app(user_input)

        except Exception as exc:
            self.report_error(
                "open app",
                exc,
            )

        return False

    # ------------------------------------------------------------------------
    # MULTI COMMAND
    # ------------------------------------------------------------------------

    def handle_multiple(
        self,
        user_input: str,
    ) -> bool:

        commands = [
            part.strip()
            for part in user_input.split(",")
            if part.strip()
        ]

        for command in commands:

            if not self.handle(command):
                break

        return self.running

    # ------------------------------------------------------------------------
    # MODES
    # ------------------------------------------------------------------------

    def run_mode(
        self,
        mode_name: str,
    ) -> bool:

        mode_name = self.normalize(mode_name)

        if mode_name not in MODES:

            self.report_error(
                "mode",
                ValueError(
                    f"Mode '{mode_name}' not found"
                ),
            )

            return self.running

        self.status(
            f"Activating {mode_name.upper()} mode...",
            "normal",
        )

        for action in MODES[mode_name]:

            if not self.running:
                break

            self.handle(action)

        return self.running

    # ------------------------------------------------------------------------
    # OPEN
    # ------------------------------------------------------------------------

    def command_open(
        self,
        argument: str,
    ):

        if not argument:

            self.status(
                "Usage → open <application>",
                "error",
            )

            return

        open_app(argument)

        self.status(
            f"Opened {argument}",
            "success",
        )

    # ------------------------------------------------------------------------
    # SITE
    # ------------------------------------------------------------------------

    def command_site(
        self,
        argument: str,
    ):

        if not argument:

            self.status(
                "Usage → site <website>",
                "error",
            )

            return

        open_site(argument)

        self.status(
            f"Opened {argument}",
            "success",
        )

    # ------------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------------

    def command_search(
        self,
        argument: str,
    ):

        if not argument:

            self.status(
                "Usage → search <query>",
                "error",
            )

            return

        google_search(argument)

        self.status(
            "Search launched",
            "success",
        )

    # ------------------------------------------------------------------------
    # ZOE
    # ------------------------------------------------------------------------

    def command_zoe(
        self,
        argument: str,
    ):

        if not argument:

            self.status(
                "Usage → zoe <command>",
                "error",
            )

            return

        self.status(
            "Contacting ZOE...",
            "processing",
        )

        payload = json.dumps(
            {
                "message": argument,
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            ZOE_CHAT_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=30,
            ) as response:

                raw_response = response.read().decode(
                    "utf-8"
                )

                data = json.loads(raw_response)

            result = (
                data.get("response")
                or data.get("result")
                or data.get("answer")
                or data.get("message")
            )

            if result:

                result = str(result).strip()

                print(f"ZOE: {result}")

                if self.zoe_response_callback:

                    self.zoe_response_callback(
                        result,
                        "success",
                    )

                self.status(
                    "ZOE RESPONDED",
                    "success",
                )

            else:

                if self.zoe_response_callback:

                    self.zoe_response_callback(
                        "ZOE returned no response.",
                        "error",
                    )

                self.status(
                    "ZOE returned no response",
                    "error",
                )

        except urllib.error.HTTPError as exc:

            details = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            error = RuntimeError(
                f"HTTP {exc.code}: {details}"
            )

            self.report_error(
                "zoe server",
                error,
            )

            if self.zoe_response_callback:

                self.zoe_response_callback(
                    f"ZOE server error: HTTP {exc.code}",
                    "error",
                )

        except urllib.error.URLError as exc:

            error = ConnectionError(
                f"Could not connect to {ZOE_CHAT_URL}: "
                f"{exc.reason}"
            )

            self.report_error(
                "zoe server",
                error,
            )

            if self.zoe_response_callback:

                self.zoe_response_callback(
                    "Could not connect to ZOE.",
                    "error",
                )

        except Exception as exc:

            self.report_error(
                "zoe server",
                exc,
            )

            if self.zoe_response_callback:

                self.zoe_response_callback(
                    f"ZOE error: {exc}",
                    "error",
                )

    # ------------------------------------------------------------------------
    # FILE SEARCH
    # ------------------------------------------------------------------------

    def command_file(
        self,
        argument: str,
    ):

        if not argument:

            self.status(
                "Usage → file <query>",
                "error",
            )

            return

        search_everything_gui(argument)

        self.status(
            "File search launched",
            "success",
        )

    # ------------------------------------------------------------------------
    # NEW PROJECT
    # ------------------------------------------------------------------------

    def command_new_project(
        self,
        argument: str,
    ):

        if getattr(sys, "frozen", False):
            # Running as ARC.exe
            base_dir = os.path.dirname(
                os.path.abspath(sys.executable)
            )
        else:
            # Running from source with Python
            base_dir = os.path.dirname(
                os.path.abspath(__file__)
            )

        creator_exe = os.path.join(
            base_dir,
            "AutoProjectCreator.exe",
        )

        if not os.path.exists(creator_exe):

            raise FileNotFoundError(
                f"AutoProjectCreator.exe not found at:\n"
                f"{creator_exe}"
            )

        subprocess.Popen(
            [creator_exe],
            cwd=base_dir,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )

    # ------------------------------------------------------------------------
    # SYSTEM
    # ------------------------------------------------------------------------

    def command_system(
        self,
        argument: str,
    ):

        action = self.normalize(argument)

        actions = {
            "shutdown": self.system_shutdown,
            "restart": self.system_restart,
            "lock": self.system_lock,
        }

        if action not in actions:

            self.status(
                "Available → shutdown / restart / lock",
                "error",
            )

            return

        actions[action]()

    # ------------------------------------------------------------------------
    # SYSTEM ACTIONS
    # ------------------------------------------------------------------------

    @staticmethod
    def system_shutdown():

        print(
            "\nARC: Shutting down system...\n"
        )

        subprocess.Popen(
            [
                "shutdown",
                "/s",
                "/t",
                "0",
            ],
            shell=False,
        )

    # ------------------------------------------------------------------------

    @staticmethod
    def system_restart():

        print(
            "\nARC: Restarting system...\n"
        )

        subprocess.Popen(
            [
                "shutdown",
                "/r",
                "/t",
                "0",
            ],
            shell=False,
        )

    # ------------------------------------------------------------------------

    @staticmethod
    def system_lock():

        print(
            "\nARC: Locking system...\n"
        )

        subprocess.Popen(
            [
                "rundll32.exe",
                "user32.dll,LockWorkStation",
            ],
            shell=False,
        )

    # ------------------------------------------------------------------------
    # EXIT
    # ------------------------------------------------------------------------

    def command_exit(
        self,
        argument: str,
    ):

        print(
            "\nARC: Shutting down...\n"
        )

        self.running = False

    # ------------------------------------------------------------------------
    # ERROR HANDLING
    # ------------------------------------------------------------------------

    def report_error(
        self,
        source: str,
        error: Exception,
    ):

        message = (
            f"{type(error).__name__}: {error}"
        )

        print(
            f"\nARC ERROR [{source}]: "
            f"{message}\n"
        )

        if self.ui_callback:

            self.ui_callback(
                f"{source.upper()} · {message}",
                "error",
            )


# ============================================================================
# ARC LAUNCHER UI
# ============================================================================

class ArcLauncher:

    def __init__(
        self,
        core: ArcCore,
    ):

        self.core = core

        self.root = tk.Tk()

        # IMPORTANT:
        # Hide the Tkinter window immediately.
        #
        # This prevents Windows from displaying the default
        # blank/white Tk window while ARC is being constructed.
        self.root.withdraw()

        self.history: list[str] = []
        self.history_index = 0

        self.current_command = ""
        self.current_argument = ""

        self._configure_window()
        self._build_ui()
        self._bind_keys()

        # Give the core a way to update the UI.
        self.core.ui_callback = self.update_status

        # Give ZOE a dedicated response channel.
        self.core.zoe_response_callback = (
            self.show_zoe_response
        )

        # Everything is now built.
        # Show the actual ARC UI.
        self.root.deiconify()

        # Focus after the window has actually appeared.
        self.root.after(
            50,
            self._focus_arc,
        )

    # ========================================================================
    # WINDOW
    # ========================================================================

    def _configure_window(self):

        self.root.title("ARC")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (
            screen_width - WINDOW_WIDTH
        ) // 2

        y = (
            (screen_height - WINDOW_HEIGHT)
            // 2
            - WINDOW_OFFSET_Y
        )

        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}"
        )

        self.root.configure(
            bg=BG_COLOR
        )

        # Borderless.
        self.root.overrideredirect(True)

        # Stay above normal windows.
        self.root.attributes(
            "-topmost",
            True,
        )

        # Slight transparency.
        try:

            self.root.attributes(
                "-alpha",
                0.98,
            )

        except tk.TclError:
            pass

    # ========================================================================
    # FOCUS
    # ========================================================================

    def _focus_arc(self):

        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes(
                "-topmost",
                True,
            )
            self.root.focus_force()
            self.entry.focus_force()
        except tk.TclError:
            pass

    # ========================================================================
    # UI
    # ========================================================================

    def _build_ui(self):

        # --------------------------------------------------------------------
        # OUTER FRAME
        # --------------------------------------------------------------------

        self.outer = tk.Frame(
            self.root,
            bg=BORDER_COLOR,
            bd=0,
            highlightthickness=0,
        )

        self.outer.pack(
            fill=tk.BOTH,
            expand=True,
        )

        # --------------------------------------------------------------------
        # INNER PANEL
        # --------------------------------------------------------------------

        self.panel = tk.Frame(
            self.outer,
            bg=PANEL_COLOR,
            bd=0,
        )

        self.panel.pack(
            fill=tk.BOTH,
            expand=True,
            padx=1,
            pady=1,
        )

        # --------------------------------------------------------------------
        # HEADER
        # --------------------------------------------------------------------

        self.header = tk.Frame(
            self.panel,
            bg=PANEL_COLOR,
            height=32,
        )

        self.header.pack(
            fill=tk.X,
        )

        self.header.pack_propagate(False)

        self.arc_label = tk.Label(
            self.header,
            text="ACTION ROUTING CORE",
            bg=PANEL_COLOR,
            fg=FG_COLOR,
            font=("Consolas", 11, "bold"),
            anchor="w",
        )

        self.arc_label.pack(
            side=tk.LEFT,
            padx=(14, 4),
        )

        self.header_divider = tk.Label(
            self.header,
            text="·",
            bg=PANEL_COLOR,
            fg=DIM_COLOR,
            font=("Consolas", 11),
        )

        self.header_divider.pack(
            side=tk.LEFT,
        )

        self.version_label = tk.Label(
            self.header,
            text=f" {VERSION}",
            bg=PANEL_COLOR,
            fg=MUTED_COLOR,
            font=FONT_SMALL,
            anchor="w",
        )

        self.version_label.pack(
            side=tk.LEFT,
        )

        self.status_label = tk.Label(
            self.header,
            text="READY",
            bg=PANEL_COLOR,
            fg=MUTED_COLOR,
            font=("Consolas", 9, "bold"),
            anchor="e",
        )

        self.status_label.pack(
            side=tk.RIGHT,
            padx=(4, 14),
        )

        # --------------------------------------------------------------------
        # SEPARATOR
        # --------------------------------------------------------------------

        self.separator = tk.Frame(
            self.panel,
            bg=BORDER_COLOR,
            height=1,
        )

        self.separator.pack(
            fill=tk.X,
        )

        # --------------------------------------------------------------------
        # INPUT AREA
        # --------------------------------------------------------------------

        self.input_container = tk.Frame(
            self.panel,
            bg=INPUT_COLOR,
        )

        self.input_container.pack(
            fill=tk.X,
            padx=10,
            pady=(10, 5),
        )

        # --------------------------------------------------------------------
        # COMMAND BADGE
        # --------------------------------------------------------------------

        self.command_badge = tk.Label(
            self.input_container,
            text="ARC",
            bg=FG_COLOR,
            fg=BG_COLOR,
            font=("Consolas", 10, "bold"),
            padx=8,
            pady=4,
            width=7,
            anchor="center",
        )

        self.command_badge.pack(
            side=tk.LEFT,
            padx=(7, 8),
            pady=7,
        )

        # --------------------------------------------------------------------
        # ENTRY
        # --------------------------------------------------------------------

        self.entry = tk.Entry(
            self.input_container,
            font=FONT_MAIN,
            bg=INPUT_COLOR,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            selectbackground="#303030",
            selectforeground=FG_COLOR,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
        )

        self.entry.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(0, 8),
            pady=8,
        )

        # --------------------------------------------------------------------
        # ZOE RESPONSE AREA
        # --------------------------------------------------------------------

        self.response_container = tk.Frame(
            self.panel,
            bg=PANEL_COLOR,
        )

        self.response_container.pack(
            fill=tk.X,
            padx=14,
            pady=(2, 4),
        )

        self.response_label = tk.Label(
            self.response_container,
            text="",
            bg=PANEL_COLOR,
            fg=FG_COLOR,
            font=FONT_HINT,
            anchor="w",
            justify=tk.LEFT,
            wraplength=680,
        )

        self.response_label.pack(
            fill=tk.X,
        )

        # --------------------------------------------------------------------
        # BOTTOM BAR
        # --------------------------------------------------------------------

        self.bottom = tk.Frame(
            self.panel,
            bg=PANEL_COLOR,
        )

        self.bottom.pack(
            fill=tk.X,
            padx=14,
            pady=(0, 7),
        )

        self.description_label = tk.Label(
            self.bottom,
            text="Type a command",
            bg=PANEL_COLOR,
            fg=MUTED_COLOR,
            font=FONT_HINT,
            anchor="w",
        )

        self.description_label.pack(
            side=tk.LEFT,
        )

        self.hints_label = tk.Label(
            self.bottom,
            text="ENTER  EXECUTE     ↑↓  HISTORY     ESC  CLOSE",
            bg=PANEL_COLOR,
            fg=DIM_COLOR,
            font=FONT_SMALL,
            anchor="e",
        )

        self.hints_label.pack(
            side=tk.RIGHT,
        )

        self.entry.bind(
            "<KeyRelease>",
            self.on_key_release,
        )

    # ========================================================================
    # KEYBOARD
    # ========================================================================

    def _bind_keys(self):

        self.entry.bind(
            "<Return>",
            self.on_enter,
        )

        self.entry.bind(
            "<Escape>",
            self.on_escape,
        )

        self.entry.bind(
            "<Up>",
            self.history_up,
        )

        self.entry.bind(
            "<Down>",
            self.history_down,
        )

    # ========================================================================
    # COMMAND PREVIEW
    # ========================================================================

    def on_key_release(
        self,
        event=None,
    ):

        text = self.entry.get().strip()

        self.update_command_preview(text)

    # ------------------------------------------------------------------------

    def update_command_preview(
        self,
        text: str,
    ):

        if not text:

            self.command_badge.configure(
                text="ARC",
                bg=FG_COLOR,
                fg=BG_COLOR,
            )

            self.description_label.configure(
                text="Type a command",
                fg=MUTED_COLOR,
            )

            self.status_label.configure(
                text="READY",
                fg=MUTED_COLOR,
            )

            return

        normalized = self.core.normalize(text)

        # --------------------------------------------------------------------
        # ZOE
        # --------------------------------------------------------------------

        if (
            normalized == "zoe"
            or normalized.startswith("zoe ")
        ):

            self.command_badge.configure(
                text="ZOE",
                bg=FG_COLOR,
                fg=BG_COLOR,
            )

            self.description_label.configure(
                text="Send command to ZOE",
                fg=FG_COLOR,
            )

            self.status_label.configure(
                text="ZOE",
                fg=FG_COLOR,
            )

            return

        # --------------------------------------------------------------------
        # MODES
        # --------------------------------------------------------------------

        if normalized in MODES:

            self.command_badge.configure(
                text=normalized.upper(),
                bg=FG_COLOR,
                fg=BG_COLOR,
            )

            self.description_label.configure(
                text=f"Activate {normalized.upper()} mode",
                fg=FG_COLOR,
            )

            self.status_label.configure(
                text="MODE",
                fg=FG_COLOR,
            )

            return

        # --------------------------------------------------------------------
        # COMMANDS
        # --------------------------------------------------------------------

        for command in self.core.commands:

            names = (
                command.name,
                *command.aliases,
            )

            for name in names:

                if (
                    normalized == name
                    or normalized.startswith(name + " ")
                ):

                    meta = COMMAND_META.get(
                        command.name,
                        {
                            "label": command.name.upper(),
                            "description": command.description,
                        },
                    )

                    self.command_badge.configure(
                        text=meta["label"],
                        bg=FG_COLOR,
                        fg=BG_COLOR,
                    )

                    self.description_label.configure(
                        text=meta["description"],
                        fg=FG_COLOR,
                    )

                    self.status_label.configure(
                        text="COMMAND",
                        fg=FG_COLOR,
                    )

                    return

        # --------------------------------------------------------------------
        # UNKNOWN / APP SHORTCUT
        # --------------------------------------------------------------------

        self.command_badge.configure(
            text="APP",
            bg="#202020",
            fg=FG_COLOR,
        )

        self.description_label.configure(
            text="Open application",
            fg=MUTED_COLOR,
        )

        self.status_label.configure(
            text="APP",
            fg=MUTED_COLOR,
        )

    # ========================================================================
    # ENTER
    # ========================================================================

    def on_enter(
        self,
        event=None,
    ):

        user_input = self.entry.get().strip()

        if not user_input:
            return "break"

        self.add_history(user_input)

        self.entry.delete(
            0,
            tk.END,
        )

        self.set_processing(
            user_input
        )

        threading.Thread(
            target=self.execute,
            args=(user_input,),
            daemon=True,
        ).start()

        return "break"

    # ========================================================================
    # EXECUTION
    # ========================================================================

    def execute(
        self,
        user_input: str,
    ):

        normalized = self.core.normalize(
            user_input
        )

        is_zoe = (
            normalized == "zoe"
            or normalized.startswith("zoe ")
        )

        try:

            if "," in user_input:

                should_continue = (
                    self.core.handle_multiple(
                        user_input
                    )
                )

            else:

                should_continue = (
                    self.core.handle(
                        user_input
                    )
                )

        except Exception as exc:

            self.core.report_error(
                "execution",
                exc,
            )

            should_continue = is_zoe

        # --------------------------------------------------------------------
        # ZOE = KEEP ARC OPEN
        # --------------------------------------------------------------------

        if is_zoe:

            self.root.after(
                0,
                self.finish_zoe_command,
            )

            return

        # --------------------------------------------------------------------
        # EVERYTHING ELSE = CLOSE ARC
        # --------------------------------------------------------------------

        self.root.after(
            0,
            self.root.destroy,
        )

    # ========================================================================
    # ZOE RESPONSE
    # ========================================================================

    def show_zoe_response(
        self,
        message: str,
        kind: str = "success",
    ):

        def update():

            if kind == "error":

                self.response_label.configure(
                    text=f"ZOE  ·  {message}",
                    fg=ERROR_COLOR,
                )

            else:

                self.response_label.configure(
                    text=f"ZOE  ·  {message}",
                    fg=FG_COLOR,
                )

        self.root.after(
            0,
            update,
        )

    # ------------------------------------------------------------------------

    def finish_zoe_command(self):

        self.status_label.configure(
            text="ZOE",
            fg=FG_COLOR,
        )

        self.command_badge.configure(
            text="ZOE",
            bg=FG_COLOR,
            fg=BG_COLOR,
        )

        self.description_label.configure(
            text="Ready for another ZOE command",
            fg=MUTED_COLOR,
        )

        self.entry.focus_force()

    # ========================================================================
    # PROCESSING STATE
    # ========================================================================

    def set_processing(
        self,
        user_input: str,
    ):

        normalized = self.core.normalize(
            user_input
        )

        is_zoe = (
            normalized == "zoe"
            or normalized.startswith("zoe ")
        )

        self.command_badge.configure(
            text="ZOE" if is_zoe else "...",
            bg=FG_COLOR,
            fg=BG_COLOR,
        )

        self.description_label.configure(
            text=(
                "Contacting ZOE..."
                if is_zoe
                else "Executing command..."
            ),
            fg=FG_COLOR,
        )

        self.status_label.configure(
            text=(
                "ZOE"
                if is_zoe
                else "RUNNING"
            ),
            fg=FG_COLOR,
        )

    # ========================================================================
    # STATUS
    # ========================================================================

    def update_status(
        self,
        message: str,
        kind: str = "normal",
    ):

        def update():

            if kind == "error":

                self.status_label.configure(
                    text="ERROR",
                    fg=ERROR_COLOR,
                )

                self.description_label.configure(
                    text=message[:75],
                    fg=ERROR_COLOR,
                )

                self.command_badge.configure(
                    text="!",
                    bg=ERROR_COLOR,
                    fg=BG_COLOR,
                )

            elif kind == "processing":

                self.status_label.configure(
                    text="PROCESSING",
                    fg=FG_COLOR,
                )

                self.description_label.configure(
                    text=message[:75],
                    fg=FG_COLOR,
                )

            elif kind == "success":

                self.status_label.configure(
                    text="DONE",
                    fg=FG_COLOR,
                )

                self.description_label.configure(
                    text=message[:75],
                    fg=MUTED_COLOR,
                )

                self.command_badge.configure(
                    text="OK",
                    bg=FG_COLOR,
                    fg=BG_COLOR,
                )

            else:

                self.status_label.configure(
                    text="READY",
                    fg=MUTED_COLOR,
                )

                self.description_label.configure(
                    text=message[:75],
                    fg=MUTED_COLOR,
                )

        self.root.after(
            0,
            update,
        )

    # ========================================================================
    # ESCAPE
    # ========================================================================

    def on_escape(
        self,
        event=None,
    ):

        self.core.running = False

        self.root.destroy()

        return "break"

    # ========================================================================
    # HISTORY
    # ========================================================================

    def add_history(
        self,
        command: str,
    ):

        if (
            not self.history
            or self.history[-1] != command
        ):

            self.history.append(
                command
            )

        self.history_index = len(
            self.history
        )

    # ------------------------------------------------------------------------

    def history_up(
        self,
        event=None,
    ):

        if not self.history:
            return "break"

        self.history_index = max(
            0,
            self.history_index - 1,
        )

        self.set_input(
            self.history[
                self.history_index
            ]
        )

        return "break"

    # ------------------------------------------------------------------------

    def history_down(
        self,
        event=None,
    ):

        if not self.history:
            return "break"

        self.history_index = min(
            len(self.history),
            self.history_index + 1,
        )

        if (
            self.history_index
            == len(self.history)
        ):

            self.set_input("")

        else:

            self.set_input(
                self.history[
                    self.history_index
                ]
            )

        return "break"

    # ------------------------------------------------------------------------

    def set_input(
        self,
        text: str,
    ):

        self.entry.delete(
            0,
            tk.END,
        )

        self.entry.insert(
            0,
            text,
        )

        self.entry.icursor(
            tk.END
        )

        self.update_command_preview(
            text
        )

    # ========================================================================
    # RUN
    # ========================================================================

    def run(self):

        self.root.mainloop()


# ============================================================================
# BOOT
# ============================================================================

def boot_screen():

    print(
        "\n"
        + "═" * 45
    )

    print(
        f"   {APP_NAME} {VERSION}"
    )

    print(
        "═" * 45
        + "\n"
    )


# ============================================================================
# MAIN
# ============================================================================

def main():

    boot_screen()

    core = ArcCore()

    launcher = ArcLauncher(
        core
    )

    launcher.run()


if __name__ == "__main__":
    main()