#Requires AutoHotkey v2.0
#SingleInstance Force
DetectHiddenWindows true

ARC_PATH := "C:\Users\hasin\Dev\ARC\dist\ARC.exe"

^Space::
{
    hwnd := WinExist("ahk_exe ARC.exe")

    if !hwnd
    {
        Run(ARC_PATH)
        return
    }

    if WinActive("ahk_id " hwnd)
    {
        WinHide("ahk_id " hwnd)
    }
    else
    {
        WinShow("ahk_id " hwnd)
        WinActivate("ahk_id " hwnd)
    }
}