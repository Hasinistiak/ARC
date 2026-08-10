import os
import subprocess

def create_py_project(name):
    base_dir = r"D:\ENAN\Documents\Dev"
    new_directory = os.path.join(base_dir, name)

    # Create the project directory
    os.makedirs(new_directory, exist_ok=True)

    # Create virtual environment
    subprocess.run(['python', '-m', 'venv', 'venv'], cwd=new_directory, shell=True)

    # Create main.py
    main_py_path = os.path.join(new_directory, "main.py")
    if not os.path.exists(main_py_path):
        with open(main_py_path, "w") as f:
            f.write("""def main():
    print("Hello from your Python project!")

if __name__ == "__main__":
    main()
""")

    # Open project in VS Code
    subprocess.run(['code', '.'], cwd=new_directory, shell=True)
