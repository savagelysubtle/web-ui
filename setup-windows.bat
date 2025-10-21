@echo off
REM Browser Use Web UI - Windows Setup Script (CMD Version)
REM This script automates the Windows installation process using UV package manager

echo 🚀 Browser Use Web UI - Windows Setup
echo =====================================

REM Check if UV is installed
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ UV is not installed. Installing UV...
    winget install astral-sh.uv
    if %errorlevel% neq 0 (
        echo ❌ Failed to install UV. Please install manually from https://github.com/astral-sh/uv/releases
        pause
        exit /b 1
    )
    echo ✅ UV installed successfully
) else (
    echo ✅ UV is already installed
)

echo.
echo 🔧 Setting up Python environment...

REM Install Python 3.14t
echo Installing Python 3.14t...
uv python install 3.14t

REM Create virtual environment
echo Creating virtual environment...
uv venv --python 3.14t

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo 📦 Installing dependencies...

REM Install dependencies using UV
echo Installing Python packages with UV...
uv sync

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install --with-deps

echo.
echo ⚙️  Setting up environment configuration...

REM Copy environment file if it doesn't exist
if not exist ".env" (
    copy ".env.example" ".env"
    echo ✅ Created .env file from template
    echo 📝 Please edit .env file with your API keys and settings
) else (
    echo ✅ .env file already exists
)

echo.
echo 🎉 Setup completed successfully!
echo =====================================

echo.
echo 📋 Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: python webui.py
echo 3. Open browser to: http://127.0.0.1:7788

echo.
echo 🚀 Quick start commands:
echo Activate environment: .venv\Scripts\activate.bat
echo Start WebUI: python webui.py

echo.
echo 💡 Tips:
echo - Use PowerShell for best experience
echo - Python 3.14t provides better performance (free-threaded)
echo - UV is much faster than pip for package management
echo - Check the README.md for detailed configuration options

echo.
echo 🎯 Ready to start! Run: python webui.py
pause
