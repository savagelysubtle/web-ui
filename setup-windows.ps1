# Browser Use Web UI - Windows Setup Script
# This script automates the Windows installation process using UV package manager

param(
    [string]$PythonVersion = "3.14t",
    [string]$Port = "7788",
    [string]$IP = "127.0.0.1",
    [string]$Theme = "Ocean"
)

Write-Host "🚀 Browser Use Web UI - Windows Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script is not running as Administrator. Some operations may require elevation."
}

# Check prerequisites
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Yellow

# Check if Git is installed
try {
    $gitVersion = git --version 2>$null
    Write-Host "✅ Git: $gitVersion" -ForegroundColor Green
} catch {
    Write-Error "❌ Git is not installed. Please install Git for Windows from https://git-scm.com/download/win"
    exit 1
}

# Check if UV is installed
try {
    $uvVersion = uv --version 2>$null
    Write-Host "✅ UV: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ UV is not installed. Installing UV..." -ForegroundColor Yellow

    # Try to install UV using winget
    try {
        winget install astral-sh.uv
        Write-Host "✅ UV installed successfully using winget" -ForegroundColor Green
    } catch {
        Write-Error "❌ Failed to install UV. Please install manually from https://github.com/astral-sh/uv/releases"
        exit 1
    }
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Python not found in PATH. UV will install it." -ForegroundColor Yellow
}

Write-Host "`n🔧 Setting up Python environment..." -ForegroundColor Yellow

# Install Python using UV
Write-Host "Installing Python $PythonVersion..."
uv python install $PythonVersion

# Create virtual environment
Write-Host "Creating virtual environment..."
uv venv --python $PythonVersion

# Activate virtual environment
Write-Host "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow

# Install dependencies using UV
Write-Host "Installing Python packages with UV..."
uv sync

# Install Playwright browsers
Write-Host "Installing Playwright browsers..."
playwright install --with-deps

Write-Host "`n⚙️  Setting up environment configuration..." -ForegroundColor Yellow

# Copy environment file if it doesn't exist
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file from template" -ForegroundColor Green
    Write-Host "📝 Please edit .env file with your API keys and settings" -ForegroundColor Cyan
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

Write-Host "`n🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your API keys" -ForegroundColor White
Write-Host "2. Run: python webui.py" -ForegroundColor White
Write-Host "3. Open browser to: http://$IP`:$Port" -ForegroundColor White

Write-Host "`n🚀 Quick start commands:" -ForegroundColor Yellow
Write-Host "Activate environment: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "Start WebUI: python webui.py" -ForegroundColor White
Write-Host "Start with custom settings: python webui.py --ip $IP --port $Port --theme $Theme" -ForegroundColor White

Write-Host "`n💡 Tips:" -ForegroundColor Yellow
Write-Host "- Use PowerShell for best experience" -ForegroundColor White
Write-Host "- Python 3.14t provides better performance (free-threaded)" -ForegroundColor White
Write-Host "- UV is much faster than pip for package management" -ForegroundColor White
Write-Host "- Check the README.md for detailed configuration options" -ForegroundColor White

Write-Host "`n🎯 Ready to start! Run: python webui.py" -ForegroundColor Green
