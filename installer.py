import os
import platform
import subprocess
import sys

APP_NAME = "SwipeNotes"
MAIN_FILE = "main.py"
ICON_PATH = "assets/icon.png"

def run(cmd_list):
    print(">", " ".join(cmd_list))
    result = subprocess.run(cmd_list)
    if result.returncode != 0:
        print(" Command failed")
        sys.exit(1)

def install_dependencies():
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build():
    system = platform.system()
    print(f" Building for {system}...")

    base_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", APP_NAME
    ]

    if os.path.exists(ICON_PATH):
        base_cmd.extend(["--icon", ICON_PATH])

    base_cmd.append(MAIN_FILE)

    run(base_cmd)

    print("\n Build complete!")
    print(" Check the 'dist/' folder")

def main():
    print(" SwipeNotes App Installer\n")
    install_dependencies()
    build()

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()