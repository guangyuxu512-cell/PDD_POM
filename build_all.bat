@echo off
chcp 65001 >nul
cd /d %~dp0

echo ========================================
echo   PDD_POM - Build All
echo ========================================

echo [1/4] Building frontend...
pushd frontend
call npm install
if errorlevel 1 goto :error
call npm run build
if errorlevel 1 goto :error
popd

echo [2/4] Packing Python backend...
call build_backend.bat
if errorlevel 1 goto :error

echo [3/4] Installing Electron deps...
pushd electron
call npm install
if errorlevel 1 goto :error

echo [4/4] Packing Electron installer...
call npm run pack
if errorlevel 1 goto :error
popd

echo ========================================
echo   Build complete
echo   Output: electron\dist\
echo ========================================
goto :end

:error
popd >nul 2>nul
echo Build failed. Check the error messages above.
exit /b 1

:end