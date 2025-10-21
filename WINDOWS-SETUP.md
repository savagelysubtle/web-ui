# Windows Setup Guide

This guide provides detailed instructions for setting up Browser Use Web UI on Windows using UV package manager for optimal performance.

## 🚀 Quick Start

### Automated Setup (Recommended)

1. **Download the setup script:**
   ```powershell
   # PowerShell (Recommended)
   .\setup-windows.ps1
   
   # Or Command Prompt
   setup-windows.bat
   ```

2. **Follow the prompts** to install UV, Python, and dependencies

3. **Edit your `.env` file** with API keys

4. **Start the application:**
   ```powershell
   python webui.py
   ```

### Manual Setup

If you prefer manual installation or encounter issues with the automated script:

#### Prerequisites

- **Windows 10/11** (64-bit)
- **PowerShell 5.1+** or **PowerShell Core 7+**
- **Git for Windows** ([Download](https://git-scm.com/download/win))

#### Step 1: Install UV Package Manager

```powershell
# Using Windows Package Manager (winget)
winget install astral-sh.uv

# Or download from GitHub releases
# https://github.com/astral-sh/uv/releases
```

#### Step 2: Clone Repository

```powershell
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

#### Step 3: Python Environment Setup

```powershell
# Install Python 3.14t (free-threaded for better performance)
uv python install 3.14t

# Create virtual environment
uv venv --python 3.14t

# Activate environment
.\.venv\Scripts\Activate.ps1
```

#### Step 4: Install Dependencies

```powershell
# Install all packages using UV (much faster than pip)
uv sync

# Install Playwright browsers
playwright install --with-deps
```

#### Step 5: Configuration

```powershell
# Copy environment template
Copy-Item .env.example .env

# Edit with your preferred editor
notepad .env
# or
code .env
```

#### Step 6: Run Application

```powershell
# Basic start
python webui.py

# With custom settings
python webui.py --ip 0.0.0.0 --port 8080 --theme Ocean
```

## 🔧 Configuration

### Environment Variables

Key settings in your `.env` file:

```env
# Default LLM Provider
DEFAULT_LLM=openai

# API Keys (add your keys)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here

# Browser Settings
USE_OWN_BROWSER=false
KEEP_BROWSER_OPEN=true
BROWSER_PATH=
BROWSER_USER_DATA=

# Performance Settings
BROWSER_USE_LOGGING_LEVEL=info
ANONYMIZED_TELEMETRY=false
```

### Using Your Own Browser

To use your existing Chrome profile:

1. **Set environment variables:**
   ```env
   USE_OWN_BROWSER=true
   BROWSER_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
   BROWSER_USER_DATA="C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data"
   ```

2. **Close all Chrome windows**

3. **Open WebUI in a different browser** (Firefox/Edge)

4. **Enable "Use Own Browser"** in Browser Settings tab

## 🛠️ Development Setup

### VS Code Configuration

The project includes VS Code configuration for optimal development experience:

- **Extensions**: Recommended extensions in `.vscode/extensions.json`
- **Settings**: Python and formatting settings in `.vscode/settings.json`
- **Tasks**: Build and test tasks in `.vscode/tasks.json`
- **Launch**: Debug configuration in `.vscode/launch.json`

### Code Quality Tools

```powershell
# Format code
ruff format .

# Lint code
ruff check .

# Fix linting issues
ruff check . --fix

# Type checking (experimental)
ty check .
```

### Testing

```powershell
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v
```

## 🚨 Troubleshooting

### Common Issues

#### UV Not Found
```powershell
# Add UV to PATH manually
$env:PATH += ";C:\Users\$env:USERNAME\.cargo\bin"
```

#### Python Version Issues
```powershell
# List available Python versions
uv python list

# Install specific version
uv python install 3.11
```

#### Playwright Browser Issues
```powershell
# Reinstall browsers
playwright install --force

# Install specific browser
playwright install chromium --with-deps
```

#### Permission Issues
```powershell
# Run PowerShell as Administrator
# Or set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Port Already in Use
```powershell
# Use different port
python webui.py --port 8080

# Or find and kill process using port 7788
netstat -ano | findstr :7788
taskkill /PID <PID> /F
```

### Performance Optimization

#### For Better Performance

1. **Use Python 3.14t** (free-threaded variant)
2. **Use UV** instead of pip for package management
3. **Enable hardware acceleration** in browser settings
4. **Use SSD storage** for better I/O performance

#### Memory Optimization

```env
# Reduce browser memory usage
BROWSER_USE_LOGGING_LEVEL=result
KEEP_BROWSER_OPEN=false
```

## 📚 Additional Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [Playwright Windows Setup](https://playwright.dev/docs/intro#windows)
- [Gradio Documentation](https://gradio.app/docs/)
- [Browser Use Documentation](https://docs.browser-use.com/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test your changes: `pytest`
5. Commit your changes: `git commit -m "Add your feature"`
6. Push to the branch: `git push origin feature/your-feature`
7. Submit a pull request

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/browser-use/web-ui/issues)
- **Discord**: [Join the community](https://link.browser-use.com/discord)
- **Documentation**: [Browse the docs](https://docs.browser-use.com)

---

**Happy browsing with AI! 🎉**
