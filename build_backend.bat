@echo off
chcp 65001 >nul
cd /d %~dp0

echo [1/2] ��� FastAPI ��� EXE...
set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
set PYTHONUTF8=1

if exist python-backend-dist rmdir /s /q python-backend-dist
if not exist build mkdir build

python -m PyInstaller --noconfirm --clean --onefile --name backend ^
  --distpath python-backend-dist ^
  --workpath build\pyinstaller\backend ^
  --specpath build\pyinstaller ^
  --hidden-import=backend ^
  --hidden-import=tasks ^
  --hidden-import=browser ^
  --hidden-import=pages ^
  --hidden-import=pdd_selectors ^
  --collect-all backend ^
  --collect-all tasks ^
  --collect-all browser ^
  --collect-all pages ^
  --collect-all pdd_selectors ^
  scripts\pyinstaller_entry.py
if errorlevel 1 goto :error

echo [2/2] ��� Celery Worker EXE...
python -m PyInstaller --noconfirm --clean --onefile --name celery-worker ^
  --distpath python-backend-dist ^
  --workpath build\pyinstaller\celery-worker ^
  --specpath build\pyinstaller ^
  --hidden-import=backend ^
  --hidden-import=tasks ^
  --hidden-import=browser ^
  --hidden-import=pages ^
  --hidden-import=pdd_selectors ^
  --collect-all backend ^
  --collect-all tasks ^
  --collect-all browser ^
  --collect-all pages ^
  --collect-all pdd_selectors ^
  --add-data "data;data" ^
  scripts\pyinstaller_celery_entry.py
if errorlevel 1 goto :error

echo �����ɣ����Ŀ¼��python-backend-dist\
goto :end

:error
echo ���ʧ�ܣ����Ȱ�װ PyInstaller �����������
exit /b 1

:end
