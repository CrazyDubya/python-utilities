#!/usr/bin/env python3
"""
Build script for creating Portsy installers for Windows and macOS
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def convert_svg_to_ico():
    """Convert SVG icon to ICO format for Windows"""
    try:
        from PIL import Image
        import cairosvg
        
        # Convert SVG to PNG first
        cairosvg.svg2png(
            url='assets/icon.svg',
            write_to='assets/icon.png',
            output_width=256,
            output_height=256
        )
        
        # Convert PNG to ICO
        img = Image.open('assets/icon.png')
        img.save('assets/icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
        print("✅ Icon converted to ICO format")
        
    except ImportError:
        print("⚠️  cairosvg not available, creating simple ICO...")
        # Create a simple colored icon as fallback
        from PIL import Image, ImageDraw
        
        img = Image.new('RGBA', (256, 256), (37, 99, 235, 255))  # Blue background
        draw = ImageDraw.Draw(img)
        
        # Draw simple port/network icon
        draw.ellipse([96, 96, 160, 160], fill=(251, 191, 36, 255))  # Yellow center
        draw.ellipse([120, 120, 136, 136], fill=(37, 99, 235, 255))  # Blue center
        
        # Add connection points
        points = [(128, 64), (164, 92), (192, 128), (164, 164), (128, 192), (92, 164), (64, 128), (92, 92)]
        for x, y in points:
            draw.ellipse([x-8, y-8, x+8, y+8], fill=(96, 165, 250, 255))
        
        img.save('assets/icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
        print("✅ Simple icon created")

def build_windows_executable():
    """Build Windows executable using PyInstaller"""
    print("🔨 Building Windows executable...")
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--console',
        '--name', 'portsy',
        '--icon', 'assets/icon.ico',
        '--add-data=README.md:.',
        '--add-data=LICENSE:.',
        'portsy.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Windows executable built successfully")
        print(f"   📁 Location: dist/portsy.exe")
    else:
        print(f"❌ Windows build failed: {result.stderr}")

def build_macos_app():
    """Build macOS app bundle using PyInstaller"""
    print("🔨 Building macOS app bundle...")
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name', 'Portsy',
        '--icon', 'assets/icon.ico',
        '--add-data', 'README.md:.',
        '--add-data', 'LICENSE:.',
        'portsy.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ macOS app bundle built successfully")
        print(f"   📁 Location: dist/Portsy.app")
    else:
        print(f"❌ macOS build failed: {result.stderr}")

def create_installer_scripts():
    """Create installer scripts for easy installation"""
    
    # Windows batch installer
    windows_installer = """@echo off
echo Installing Portsy...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Install Portsy
echo Installing Portsy via pip...
pip install psutil requests
if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

REM Copy executable to a standard location
if not exist "%USERPROFILE%\\AppData\\Local\\Portsy" mkdir "%USERPROFILE%\\AppData\\Local\\Portsy"
copy portsy.exe "%USERPROFILE%\\AppData\\Local\\Portsy\\"

REM Add to PATH (requires admin rights)
echo.
echo To use 'portsy' command globally, add the following to your PATH:
echo %USERPROFILE%\\AppData\\Local\\Portsy
echo.
echo Installation complete!
echo Run: portsy --help
pause
"""

    # macOS/Linux shell installer
    unix_installer = """#!/bin/bash

echo "🚀 Installing Portsy..."
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH."
    echo "Please install Python 3 from https://python.org"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install psutil requests
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Copy to /usr/local/bin (requires sudo)
echo "🔧 Installing portsy command..."
if [ "$(uname)" == "Darwin" ]; then
    # macOS
    if [ -f "dist/Portsy.app/Contents/MacOS/Portsy" ]; then
        sudo cp dist/Portsy.app/Contents/MacOS/Portsy /usr/local/bin/portsy
    else
        sudo cp portsy.py /usr/local/bin/portsy
    fi
else
    # Linux
    sudo cp portsy.py /usr/local/bin/portsy
fi

sudo chmod +x /usr/local/bin/portsy

echo "✅ Installation complete!"
echo "Run: portsy --help"
"""

    # Write installer scripts
    with open('installers/install_windows.bat', 'w') as f:
        f.write(windows_installer)
    
    with open('installers/install_unix.sh', 'w') as f:
        f.write(unix_installer)
    
    # Make Unix installer executable
    os.chmod('installers/install_unix.sh', 0o755)
    
    print("✅ Installer scripts created")
    print("   📁 Windows: installers/install_windows.bat")
    print("   📁 Unix: installers/install_unix.sh")

def main():
    """Main build process"""
    print("🏗️  Building Portsy Installers")
    print("=" * 40)
    
    # Create directories
    os.makedirs('assets', exist_ok=True)
    os.makedirs('installers', exist_ok=True)
    os.makedirs('dist', exist_ok=True)
    
    # Convert icon
    convert_svg_to_ico()
    
    # Build executables
    build_windows_executable()
    
    if sys.platform == 'darwin':
        build_macos_app()
    
    # Create installer scripts
    create_installer_scripts()
    
    print("\n🎉 Build process complete!")
    print("\nCreated files:")
    print("📁 dist/portsy.exe (Windows)")
    if sys.platform == 'darwin':
        print("📁 dist/Portsy.app (macOS)")
    print("📁 installers/install_windows.bat")
    print("📁 installers/install_unix.sh")

if __name__ == "__main__":
    main()