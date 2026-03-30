@echo off
chcp 65001 >nul
cd /d %~dp0

echo ========================================
echo   自动化工作台 - 一键打包
echo ========================================

echo [1/4] 构建前端...
pushd frontend
call npm install
if errorlevel 1 goto :error
call npm run build
if errorlevel 1 goto :error
popd

echo [2/4] 打包 Python 后端...
call build_backend.bat
if errorlevel 1 goto :error

echo [3/4] 安装 Electron 依赖...
pushd electron
call npm install
if errorlevel 1 goto :error

echo [4/4] 打包 Electron 安装包...
call npm run pack
if errorlevel 1 goto :error
popd

echo ========================================
echo   打包完成
echo   输出目录: electron\dist\
echo ========================================
goto :end

:error
popd >nul 2>nul
echo 打包失败，请根据上面的报错信息排查。
exit /b 1

:end
