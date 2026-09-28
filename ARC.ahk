#Requires AutoHotkey v2.0
#SingleInstance Force

ARC_PATH := "C:\Users\hasin\Dev\ARC\dist\ARC.exe"

^Space::
{
    ; Look for the visible ARC window.
    ; DetectHiddenWindows is intentionally NOT enabled.
    hwnd := WinExist("ahk_exe ARC.exe")

    ; ------------------------------------------------------------
    ; ARC is not running
    ; ------------------------------------------------------------

    if !hwnd
    {
        Run(ARC_PATH)

        ; Wait for ARC to create its window.
        if WinWait("ahk_exe ARC.exe",, 5)
        {
            hwnd := WinExist("ahk_exe ARC.exe")

            ; Give Tkinter a moment to finish deiconify/focus.
            Sleep(150)

            WinShow("ahk_id " hwnd)
            WinActivate("ahk_id " hwnd)
        }

        return
    }

    ; ------------------------------------------------------------
    ; ARC is already focused
    ; → hide it
    ; ------------------------------------------------------------

    if WinActive("ahk_id " hwnd)
    {
        WinHide("ahk_id " hwnd)
        return
    }

    ; ------------------------------------------------------------
    ; ARC exists but isn't focused
    ; → show + activate
    ; ------------------------------------------------------------

    WinShow("ahk_id " hwnd)
    WinActivate("ahk_id " hwnd)
}