import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build Windows executable for SuperScribe"""
    print("Building SuperScribe Windows Executable...")
    
    # Create icon first if it doesn't exist
    if not os.path.exists("superscribe_icon.png"):
        print("Generating application icon...")
        import icon
        icon.create_icon()
    
    # Convert PNG icon to ICO for Windows
    try:
        from PIL import Image
        img = Image.open("superscribe_icon.png")
        icon_path = "superscribe_icon.ico"
        img.save(icon_path, format="ICO", sizes=[(32, 32)])
        print(f"Created ICO file: {icon_path}")
    except Exception as e:
        print(f"Warning: Could not create ICO file: {str(e)}")
        icon_path = "superscribe_icon.png"
    
    # Ensure clean build
    print("Cleaning previous build files...")
    for path in ["build", "dist", "superscribe.spec"]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    
    # Build command for PyInstaller
    command = [
        "pyinstaller",
        "--onefile",                   # Create a single EXE file
        "--windowed",                  # Windows app (not console)
        f"--icon={icon_path}",         # Application icon
        "--name=SuperScribe",          # Name of the executable
        "--add-data=superscribe_icon.png;.",  # Include icon
        "--hidden-import=PIL._tkinter_finder",  # Fix potential PIL/Tkinter issue
        "superscribe_win.py"           # Main script
    ]
    
    # Run PyInstaller
    print("Running PyInstaller...")
    try:
        subprocess.run(command, check=True)
        print("\nBuild successful!")
        print(f"Executable created: {os.path.join('dist', 'SuperScribe.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {str(e)}")
        return False
    
    # Copy additional files to dist folder
    try:
        # Create .env file in dist if it doesn't exist
        env_file = os.path.join("dist", ".env")
        if not os.path.exists(env_file):
            with open(env_file, "w") as f:
                with open(".env", "r") as source_env:
                    f.write(source_env.read())
        
        # Create recordings directory
        recordings_dir = os.path.join("dist", "recordings")
        Path(recordings_dir).mkdir(exist_ok=True)
        
        print("Additional files and folders copied to distribution directory.")
    except Exception as e:
        print(f"Warning: Could not copy additional files: {str(e)}")
    
    return True

if __name__ == "__main__":
    build_executable() 