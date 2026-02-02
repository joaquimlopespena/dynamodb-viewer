@echo off
REM Script de instalação do DynamoDB Viewer para Windows

echo.
echo ========================================
echo   DynamoDB Viewer - Setup (Windows)
echo ========================================
echo.

REM Verifica Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Instale Python 3.6 ou superior.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version

REM Verifica AWS CLI
aws --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [AVISO] AWS CLI nao encontrado.
    echo.
    echo Instale o AWS CLI:
    echo   Download: https://aws.amazon.com/cli/
    echo.
    set /p continuar="Deseja continuar sem AWS CLI? (S/N): "
    if /i not "%continuar%"=="S" exit /b 1
) else (
    echo [OK] AWS CLI encontrado
    aws --version
)

REM Instala dependências
echo.
echo Instalando dependencias Python...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)

echo [OK] Dependencias instaladas!

REM Verifica configuração AWS
echo.
aws configure get aws_access_key_id >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] AWS CLI nao configurado.
    echo.
    set /p configurar="Deseja configurar agora? (S/N): "
    if /i "%configurar%"=="S" aws configure
) else (
    echo [OK] AWS CLI ja configurado!
)

echo.
echo ========================================
echo   Setup concluido!
echo ========================================
echo.
echo Para iniciar o aplicativo, execute:
echo   python dynamodb_viewer.py
echo.
echo Ou crie um arquivo .bat para facilitar:
echo   @echo off
echo   python "%~dp0dynamodb_viewer.py"
echo.
pause
