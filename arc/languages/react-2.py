import os
import subprocess

def create_react_project(name):
    base_dir = r"D:\ENAN\Documents\Dev"
    new_directory = os.path.join(base_dir, name)

    # Run the create-react-app command
    subprocess.run(['npx', 'create-react-app', name], cwd=base_dir, shell=True)

    # Open the project in VS Code
    subprocess.run(['code', '.'], cwd=new_directory, shell=True)
