import os
import subprocess

def create_cpp_project(name):
    base_dir = r"D:\ENAN\Documents\Dev"
    new_directory = os.path.join(base_dir, name)

    # Create project root
    os.makedirs(new_directory, exist_ok=True)

    # Create subfolders
    os.makedirs(os.path.join(new_directory, "src"), exist_ok=True)
    os.makedirs(os.path.join(new_directory, "include"), exist_ok=True)
    os.makedirs(os.path.join(new_directory, "build"), exist_ok=True)

    # Create default files
    main_cpp_path = os.path.join(new_directory, "src", "main.cpp")
    header_path = os.path.join(new_directory, "include", "myheader.h")

    if not os.path.exists(main_cpp_path):
        with open(main_cpp_path, "w") as f:
            f.write("""#include <iostream>
int main() {
    std::cout << "Hello, C++!" << std::endl;
    return 0;
}
""")

    if not os.path.exists(header_path):
        with open(header_path, "w") as f:
            f.write("// myheader.h\n")

    # Open in VS Code
    subprocess.run(["code", "."], cwd=new_directory, shell=True)
