import tkinter as tk
import os
from languages.python import create_py_project
from languages.react import create_react_project
from languages.rust import create_rust_project

from languages.cpp import create_cpp_project
from languages.reactnative import create_reactnative_project

root = tk.Tk()
root.configure(bg='#1a1a1a')
root.geometry("270x245")
root.title("Project Creator")

# Windows path
dev_directory = r'D:\ENAN\Documents\Dev'

# Make sure the path exists
if not os.path.exists(dev_directory):
    os.makedirs(dev_directory)

# Get folder names in directory (case-insensitive)
projects_in_directory = [f.lower() for f in os.listdir(dev_directory) if os.path.isdir(os.path.join(dev_directory, f))]

langs = ["Python", "C++", "React", "React Native", "Rust", "Tauri"]
letters_list = [chr(c) for c in range(ord('a'), ord('z') + 1)]

selected_lang = tk.StringVar()
selected_lang.set(langs[0])

label1 = tk.Label(root, text="Enter A Project Name", font=('Inter', 15, 'bold'), bg='#1a1a1a', fg='#00c8ff')
label1.grid(row=0, column=0, padx=30, pady=10, sticky='ew')

entry1 = tk.Entry(root, font=('Inter', 13), bg='#232323', fg='#00c8ff', insertbackground='#00c8ff',
                  relief='flat', borderwidth=0)
entry1.grid(row=1, column=0, padx=30, pady=10, sticky='ew')

label2 = tk.Label(root, text="Select a Language", font=('Inter', 15, 'bold'), bg='#1a1a1a', fg='#00c8ff')
label2.grid(row=2, column=0, padx=30, pady=10, sticky='ew')

entry2 = tk.OptionMenu(root, selected_lang, *langs)
entry2.config(bg='#232323', fg='#00c8ff', activebackground='#2d5a6e', activeforeground='#00c8ff', relief='flat', borderwidth=0)
entry2['menu'].config(bg='#232323', fg='#00c8ff', activebackground='#2d5a6e', activeforeground='#ffffff')
entry2.grid(row=3, column=0, padx=30, pady=10, sticky='ew')

def setName():
    return entry1.get().strip()

def setLang():
    return selected_lang.get()

def onclick():
    lang = setLang()
    name = setName().lower()

    os.chdir(dev_directory)

    print("Creating Project...") 
    if lang == 'Python' and name:
        create_py_project(name)
    elif lang == 'React' and name:
        create_react_project(name)
    elif lang == 'Rust' and name:
        create_rust_project(name)
    elif lang == 'C++' and name:
        create_cpp_project(name)
    elif lang == 'React Native' and name:
        create_reactnative_project(name)
    print("Initialized Project") 

message_label = tk.Label(root, font=('Inter', 15, 'bold'), bg='#1a1a1a')

def update_button_state():
    name = setName().lower()

    button.grid_remove()
    message_label.grid_remove()

    if not name:
        return

    if name in projects_in_directory:
        message_label.config(text="Name Exists", fg='#FF0000')
        message_label.grid(row=4, column=0, padx=30, pady=10, sticky='ew')
    elif not (name[0] in letters_list or name.startswith('_')):
        message_label.config(text="Name Not Possible", fg='#FF0000')
        message_label.grid(row=4, column=0, padx=30, pady=10, sticky='ew')
    else:
        button.grid(row=4, column=0, padx=30, pady=10, sticky='ew')

button = tk.Button(root, text="INITIALIZE PROJECT", font=('Inter', 10),
                   command=onclick, bg='#232323', fg='#00c8ff',
                   activebackground='#2d5a6e', activeforeground='#ffffff',
                   relief='flat', borderwidth=0)

entry1.bind('<KeyRelease>', lambda e: update_button_state())
selected_lang.trace('w', lambda *args: update_button_state())

update_button_state()
root.mainloop()
