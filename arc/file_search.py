import subprocess
import time
import pyautogui

def search_everything_gui(query):

    subprocess.Popen(r"C:\Program Files (x86)\Everything\Everything.exe")
    
    time.sleep(0.5)
    
    pyautogui.write(query, interval=0.02)
    
    pyautogui.press("enter")

