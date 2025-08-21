@echo off
echo.
echo ██████╗ ███████╗███████╗██████╗  ██████╗ ███████╗███╗   ███╗
echo ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗ ████║
echo ██║  ██║█████╗  █████╗  ██████╔╝██║  ███╗█████╗  ██╔████╔██║
echo ██║  ██║██╔══╝  ██╔══╝  ██╔═══╝ ██║   ██║██╔══╝  ██║╚██╔╝██║
echo ██████╔╝███████╗███████╗██║     ╚██████╔╝███████╗██║ ╚═╝ ██║
echo ╚═════╝ ╚══════╝╚══════╝╚═╝      ╚═════╝ ╚══════╝╚═╝     ╚═╝
echo                    Quick Installer
echo.

echo [1/5] Installing deepgem...
pip install -e %~dp0 >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Failed to install deepgem. Make sure Python is installed.
    pause
    exit /b 1
)

echo [2/5] Creating command shortcuts...
echo @python -m deepgem %%* > "%USERPROFILE%\deepgem.bat"
echo @python -m deepgem gem -p "%%*" --include-directories . > "%USERPROFILE%\dg.bat"

echo [3/5] Adding to PATH permanently...
:: Check if already in PATH to avoid duplicates
echo %PATH% | find /i "%USERPROFILE%" >nul || setx PATH "%PATH%;%USERPROFILE%" >nul 2>&1
echo %PATH% | find /i "%APPDATA%\npm" >nul || setx PATH "%PATH%;%APPDATA%\npm" >nul 2>&1

echo [4/5] Checking for Node.js/npm...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  npm not found - Gemini CLI features will be limited
    echo    Install Node.js from https://nodejs.org/
) else (
    echo [5/5] Installing Gemini CLI...
    npm install -g @google/gemini-cli >nul 2>&1
    if %errorlevel% eq 0 (
        echo ✅ Gemini CLI installed!
    ) else (
        echo ⚠️  Gemini CLI install failed - try: npm install -g @google/gemini-cli
    )
)

echo.
echo ════════════════════════════════════════════════════════════
echo ✅ Installation complete!
echo ════════════════════════════════════════════════════════════
echo.
echo ⚠️  IMPORTANT: Close this terminal and open a NEW one!
echo.
echo Then set up your API keys:
echo   set DEEPSEEK_API_KEY=sk-your-key-here
echo   gemini auth  (or set GEMINI_API_KEY=your-key)
echo.
echo Usage:
echo   deepgem chat "hello"          - Chat with DeepSeek
echo   dg "analyze this code"        - Analyze code with Gemini
echo   deepgem doctor                - Check your setup
echo.
pause