import os
import subprocess

def create_rust_project(name):
    base_dir = r"D:\ENAN\Documents\Dev"
    new_directory = os.path.join(base_dir, name)

    # Create a new Rust project
    subprocess.run(['cargo', 'new', name], cwd=base_dir, shell=True)

    # Open it in VS Code
    subprocess.run(['code', '.'], cwd=new_directory, shell=True)
