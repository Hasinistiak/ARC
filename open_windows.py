from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass


# ============================================================================
# WINDOW MODEL
# ============================================================================

@dataclass
class WindowInfo:
    hwnd: int
    title: str
    process_name: str
    process_path: str = ""

    @property
    def display_name(self) -> str:
        return self.title or self.process_name


# ============================================================================
# WINDOWS API
# ============================================================================

if os.name == "nt":

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )

    user32.EnumWindows.argtypes = [
        EnumWindowsProc,
        ctypes.c_void_p,
    ]

    user32.EnumWindows.restype = ctypes.c_bool

    user32.IsWindowVisible.argtypes = [
        ctypes.c_void_p,
    ]

    user32.IsWindowVisible.restype = ctypes.c_bool

    user32.GetWindowTextLengthW.argtypes = [
        ctypes.c_void_p,
    ]

    user32.GetWindowTextLengthW.restype = ctypes.c_int

    user32.GetWindowTextW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_int,
    ]

    user32.GetWindowThreadProcessId.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_ulong),
    ]

    user32.GetWindowThreadProcessId.restype = ctypes.c_ulong

    user32.GetShellWindow.argtypes = []
    user32.GetShellWindow.restype = ctypes.c_void_p

    user32.ShowWindow.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
    ]

    user32.ShowWindow.restype = ctypes.c_bool

    user32.SetForegroundWindow.argtypes = [
        ctypes.c_void_p,
    ]

    user32.SetForegroundWindow.restype = ctypes.c_bool

    user32.BringWindowToTop.argtypes = [
        ctypes.c_void_p,
    ]

    user32.BringWindowToTop.restype = ctypes.c_bool

    user32.IsIconic.argtypes = [
        ctypes.c_void_p,
    ]

    user32.IsIconic.restype = ctypes.c_bool

    user32.GetWindowLongW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
    ]

    user32.GetWindowLongW.restype = ctypes.c_long

    # PROCESS_QUERY_LIMITED_INFORMATION
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    kernel32.OpenProcess.argtypes = [
        ctypes.c_uint,
        ctypes.c_bool,
        ctypes.c_uint,
    ]

    kernel32.OpenProcess.restype = ctypes.c_void_p

    kernel32.QueryFullProcessImageNameW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_wchar_p,
        ctypes.POINTER(ctypes.c_uint),
    ]

    kernel32.QueryFullProcessImageNameW.restype = ctypes.c_bool

    kernel32.CloseHandle.argtypes = [
        ctypes.c_void_p,
    ]

    kernel32.CloseHandle.restype = ctypes.c_bool

    # ShowWindow constants
    SW_RESTORE = 9

    # Extended window styles
    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080


# ============================================================================
# WINDOWS WE DO NOT WANT IN ARC NAVIGATION
# ============================================================================

EXCLUDED_PROCESS_NAMES = {
    "textinputhost.exe",
    "searchhost.exe",
    "startmenuexperiencehost.exe",
    "shellexperiencehost.exe",
    "lockapp.exe",
    "applicationframehost.exe",
}

EXCLUDED_WINDOW_TITLES = {
    "text input host",
    "windows input experience",
}


# ============================================================================
# PROCESS HELPERS
# ============================================================================

def _get_process_path(pid: int) -> str:
    """
    Return the executable path for a Windows process.

    Some protected/system processes may reject the query.
    In that case an empty string is returned.
    """

    if os.name != "nt":
        return ""

    handle = kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid,
    )

    if not handle:
        return ""

    try:
        buffer_size = 1024

        buffer = ctypes.create_unicode_buffer(
            buffer_size
        )

        size = ctypes.c_uint(
            buffer_size
        )

        success = kernel32.QueryFullProcessImageNameW(
            handle,
            0,
            buffer,
            ctypes.byref(size),
        )

        if success:
            return buffer.value

    except Exception:
        pass

    finally:
        kernel32.CloseHandle(
            handle
        )

    return ""


# ============================================================================
# OPEN WINDOW DISCOVERY
# ============================================================================

def get_open_windows() -> list[WindowInfo]:
    """
    Return all visible, user-facing application windows.

    ARC itself, Windows shell/tool windows, Text Input Host,
    and other internal Windows surfaces are excluded.
    """

    if os.name != "nt":
        return []

    results: list[WindowInfo] = []

    arc_pid = os.getpid()

    shell_window = user32.GetShellWindow()

    def enum_callback(
        hwnd,
        lparam,
    ):
        # ------------------------------------------------------------
        # Visibility
        # ------------------------------------------------------------

        if not user32.IsWindowVisible(hwnd):
            return True

        # ------------------------------------------------------------
        # Get owning process
        # ------------------------------------------------------------

        pid = ctypes.c_ulong()

        user32.GetWindowThreadProcessId(
            hwnd,
            ctypes.byref(pid),
        )

        process_id = pid.value

        # ------------------------------------------------------------
        # Never show ARC itself
        # ------------------------------------------------------------

        if process_id == arc_pid:
            return True

        # ------------------------------------------------------------
        # Ignore Windows desktop
        # ------------------------------------------------------------

        if hwnd == shell_window:
            return True

        # ------------------------------------------------------------
        # Ignore tool windows
        # ------------------------------------------------------------

        exstyle = user32.GetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
        )

        if exstyle & WS_EX_TOOLWINDOW:
            return True

        # ------------------------------------------------------------
        # Window title
        # ------------------------------------------------------------

        title_length = user32.GetWindowTextLengthW(
            hwnd
        )

        if title_length <= 0:
            return True

        buffer = ctypes.create_unicode_buffer(
            title_length + 1
        )

        user32.GetWindowTextW(
            hwnd,
            buffer,
            title_length + 1,
        )

        title = buffer.value.strip()

        if not title:
            return True

        # ------------------------------------------------------------
        # Process information
        # ------------------------------------------------------------

        process_path = _get_process_path(
            process_id
        )

        process_name = ""

        if process_path:
            process_name = os.path.basename(
                process_path
            )

        process_name_lower = (
            process_name.lower()
        )

        title_lower = title.lower()

        # ------------------------------------------------------------
        # Explicit Windows internal exclusions
        # ------------------------------------------------------------

        if (
            process_name_lower
            in EXCLUDED_PROCESS_NAMES
        ):
            return True

        if (
            title_lower
            in EXCLUDED_WINDOW_TITLES
        ):
            return True

        # ------------------------------------------------------------
        # Extra Text Input Host protection
        #
        # Some Windows versions expose slightly different names.
        # ------------------------------------------------------------

        if (
            "text input host"
            in title_lower
        ):
            return True

        if (
            "windows input experience"
            in title_lower
        ):
            return True

        # ------------------------------------------------------------
        # Store window
        # ------------------------------------------------------------

        results.append(
            WindowInfo(
                hwnd=int(hwnd),
                title=title,
                process_name=(
                    process_name
                    or "Unknown"
                ),
                process_path=process_path,
            )
        )

        return True

    callback = EnumWindowsProc(
        enum_callback
    )

    user32.EnumWindows(
        callback,
        0,
    )

    # ------------------------------------------------------------
    # Deduplicate HWNDs
    # ------------------------------------------------------------

    unique: dict[int, WindowInfo] = {}

    for window in results:
        unique[window.hwnd] = window

    windows = list(
        unique.values()
    )

    # ------------------------------------------------------------
    # Stable alphabetical ordering.
    #
    # This makes ↑ / ↓ navigation predictable.
    # ------------------------------------------------------------

    windows.sort(
        key=lambda window: (
            window.display_name.lower(),
            window.process_name.lower(),
        )
    )

    return windows


# ============================================================================
# ACTIVATE WINDOW
# ============================================================================

def activate_window(
    window: WindowInfo,
) -> bool:
    """
    Restore and bring a selected window to the foreground.
    """

    if os.name != "nt":
        return False

    hwnd = window.hwnd

    try:
        # ------------------------------------------------------------
        # Restore minimized windows
        # ------------------------------------------------------------

        if user32.IsIconic(hwnd):

            user32.ShowWindow(
                hwnd,
                SW_RESTORE,
            )

        # ------------------------------------------------------------
        # Bring to front
        # ------------------------------------------------------------

        user32.BringWindowToTop(
            hwnd
        )

        success = user32.SetForegroundWindow(
            hwnd
        )

        return bool(success)

    except Exception:
        return False