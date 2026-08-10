import os
import subprocess

def create_reactnative_project(name):
    base_dir = r"D:\ENAN\Documents\Dev"
    new_directory = os.path.join(base_dir, name)

    # Create the Expo React Native project
    subprocess.run(['npx', 'create-expo-app', name], cwd=base_dir, shell=True)

    # Open the project in VS Code
    subprocess.run(['code', '.'], cwd=new_directory, shell=True)
