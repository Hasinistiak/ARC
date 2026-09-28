from __future__ import annotations

import difflib
import os
import re
import subprocess
from pathlib import Path


# ============================================================
# ARC APPLICATION DISCOVERY
# ============================================================

apps: dict[str, str] = {}


def normalize_name(name: str) -> str:
    """
    Normalize an application name for matching.
    """

    name = Path(name).stem

    name = name.lower().strip()

    # Remove common shortcut suffixes
    name = re.sub(r"\s*-\s*shortcut$", "", name, flags=re.I)

    # Normalize separators
    name = re.sub(r"[_\-]+", " ", name)

    # Collapse whitespace
    name = re.sub(r"\s+", " ", name)

    return name.strip()


def add_app(name: str, target: str):
    """
    Add an application to the ARC database.
    """

    if not name or not target:
        return

    name = normalize_name(name)

    if not name:
        return

    target = str(target).strip()

    if not target:
        return

    # Don't overwrite an existing working entry.
    if name not in apps:
        apps[name] = target


# ============================================================
# START MENU DISCOVERY
# ============================================================

def discover_start_menu_apps():
    locations = [
        Path(
            os.environ.get("PROGRAMDATA", "")
        ) / "Microsoft" / "Windows" / "Start Menu" / "Programs",

        Path(
            os.environ.get("APPDATA", "")
        ) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]

    for location in locations:

        if not location.exists():
            continue

        try:
            for file in location.rglob("*"):

                if not file.is_file():
                    continue

                suffix = file.suffix.lower()

                if suffix in {".lnk", ".url"}:
                    add_app(file.stem, str(file))

        except (PermissionError, OSError):
            continue


# ============================================================
# COMMON EXE LOCATIONS
# ============================================================

def discover_executables():
    locations = []

    env_locations = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("LOCALAPPDATA"),
        os.environ.get("APPDATA"),
    ]

    for location in env_locations:

        if location:
            locations.append(Path(location))

    # Common Windows application locations
    locations.extend([
        Path(os.environ.get("SystemDrive", "C:")) / "Program Files",
        Path(os.environ.get("SystemDrive", "C:")) / "Program Files (x86)",
    ])

    seen = set()

    for root in locations:

        if not root.exists():
            continue

        root_key = str(root).lower()

        if root_key in seen:
            continue

        seen.add(root_key)

        try:

            # Don't recursively scan every single file on the disk.
            # Search only a few levels deep.
            for exe in root.glob("*/*.exe"):

                if exe.is_file():
                    add_app(exe.stem, str(exe))

            for exe in root.glob("*/*/*.exe"):

                if exe.is_file():
                    add_app(exe.stem, str(exe))

        except (PermissionError, OSError):
            continue


# ============================================================
# WINDOWS APP PATHS REGISTRY
# ============================================================

def discover_registry_apps():
    """
    Discover applications registered through Windows App Paths.

    This catches applications that don't necessarily have
    Start Menu shortcuts.
    """

    try:

        import winreg

    except ImportError:
        return

    registry_roots = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
        ),
    ]

    for root, key_path in registry_roots:

        try:

            with winreg.OpenKey(root, key_path) as key:

                count = winreg.QueryInfoKey(key)[0]

                for i in range(count):

                    try:

                        subkey_name = winreg.EnumKey(key, i)

                        with winreg.OpenKey(
                            key,
                            subkey_name
                        ) as subkey:

                            executable = winreg.QueryValue(
                                subkey,
                                ""
                            )

                            if executable:
                                add_app(
                                    Path(subkey_name).stem,
                                    executable
                                )

                    except (OSError, FileNotFoundError):
                        continue

        except (OSError, FileNotFoundError):
            continue


# ============================================================
# MICROSOFT STORE / UWP / MSIX APPS
# ============================================================

def discover_windows_apps():
    """
    Discover Windows Store / UWP / MSIX applications.

    Uses PowerShell's Get-StartApps, which exposes apps that
    aren't ordinary .exe files.
    """

    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "Get-StartApps | ConvertTo-Json -Compress",
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode != 0:
            return

        output = result.stdout.strip()

        if not output:
            return

        import json

        data = json.loads(output)

        if isinstance(data, dict):
            data = [data]

        for item in data:

            if not isinstance(item, dict):
                continue

            name = item.get("Name")
            app_id = item.get("AppID")

            if not name or not app_id:
                continue

            # For Store apps, the Start Menu shell URI is often
            # more reliable than trying to locate an EXE.
            add_app(
                name,
                f"shell:AppsFolder\\{app_id}"
            )

    except (
        subprocess.SubprocessError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ):
        pass


# ============================================================
# SPECIAL WINDOWS APPLICATIONS
# ============================================================

def add_windows_commands():

    special_apps = {
        "files": "explorer.exe",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",

        "notepad": "notepad.exe",

        "calculator": "calc.exe",

        "cmd": "cmd.exe",

        "command prompt": "cmd.exe",

        "powershell": "powershell.exe",

        "terminal": "wt.exe",

        "windows terminal": "wt.exe",

        "settings": "ms-settings:",

        "control panel": "control.exe",

        "task manager": "taskmgr.exe",

        "paint": "mspaint.exe",

        "snipping tool": "snippingtool.exe",
    }

    for name, target in special_apps.items():
        add_app(name, target)


# ============================================================
# BUILD DATABASE
# ============================================================

def discover_apps():

    apps.clear()

    # Highest confidence / most useful sources first.
    add_windows_commands()
    discover_start_menu_apps()
    discover_registry_apps()
    discover_windows_apps()
    discover_executables()

    return apps


# Build the initial database.
discover_apps()


# ============================================================
# FUZZY MATCHING
# ============================================================

def find_best_match(user_input, choices):

    user_input = normalize_name(user_input)

    # Exact match
    if user_input in choices:
        return user_input

    # Exact substring
    for choice in choices:

        if user_input in choice:
            return choice

    # Fuzzy match
    matches = difflib.get_close_matches(
        user_input,
        choices,
        n=1,
        cutoff=0.45,
    )

    return matches[0] if matches else None


# ============================================================
# OPEN APPLICATION
# ============================================================

def open_app(app_name):

    app_name = normalize_name(app_name)

    if not app_name:
        return False

    # --------------------------------------------------------
    # Direct match
    # --------------------------------------------------------

    if app_name in apps:

        target = app_name

    else:

        # ----------------------------------------------------
        # Fuzzy match
        # ----------------------------------------------------

        target = find_best_match(
            app_name,
            apps.keys(),
        )

        if not target:

            print(f"ARC: Unknown app: {app_name}")

            return False

    path = apps[target]

    # --------------------------------------------------------
    # Launch
    # --------------------------------------------------------

    try:

        print(f"ARC: Opening {target}...")

        # Windows shell handles:
        #
        # .exe
        # .lnk
        # shell:AppsFolder
        # ms-settings:
        # .url
        #
        # much better than subprocess for this use case.

        os.startfile(path)

        return True

    except FileNotFoundError:

        print(
            f"ARC: Application target not found: {path}"
        )

        return False

    except OSError as e:

        print(
            f"ARC: Could not open {target}: {e}"
        )

        return False


# ============================================================
# REFRESH
# ============================================================

def refresh_apps():

    discover_apps()

    print(
        f"ARC: Discovered {len(apps)} applications."
    )


# ============================================================
# LIST
# ============================================================

def list_apps():

    print(
        f"\nARC: {len(apps)} applications discovered.\n"
    )

    for name in sorted(apps):

        print(
            f"  {name} -> {apps[name]}"
        )


# ============================================================
# DEBUG
# ============================================================

if __name__ == "__main__":

    print(
        f"ARC discovered {len(apps)} applications:\n"
    )

    for name in sorted(apps):

        print(
            f"{name} -> {apps[name]}"
        )