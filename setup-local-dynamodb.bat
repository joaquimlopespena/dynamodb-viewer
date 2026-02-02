@echo off
REM Setup script for DynamoDB Local on Windows

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     DynamoDB Viewer - Setup para DynamoDB Local            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker não está instalado!
    echo.
    echo Por favor, instale Docker em:
    echo    https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✓ Docker encontrado
echo.

REM Menu
echo ╔════════════════════════════════════════════════════════════╗
echo ║ OPÇÕES DE INICIALIZAÇÃO                                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 1) Iniciar DynamoDB Local em container Docker
echo 2) Parar DynamoDB Local
echo 3) Ver logs do container
echo 4) Sair
echo.
set /p choice=Escolha uma opção (1-4): 

if "%choice%"=="1" (
    echo.
    echo Iniciando DynamoDB Local...
    docker run -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local:latest
    
    if %errorlevel% equ 0 (
        echo ✓ DynamoDB Local iniciado com sucesso!
        echo.
        echo Endpoint: http://localhost:9000
        echo.
        echo Você pode agora executar:
        echo   main.py
    ) else (
        echo ❌ Erro ao iniciar container
        echo Talvez já exista um container com esse nome
        echo Tente: docker rm dynamodb-local
    )
) else if "%choice%"=="2" (
    echo.
    echo Parando DynamoDB Local...
    docker stop dynamodb-local
    docker rm dynamodb-local
    echo ✓ DynamoDB Local parado
) else if "%choice%"=="3" (
    echo.
    echo Logs do DynamoDB Local:
    echo ========================
    docker logs -f dynamodb-local
) else if "%choice%"=="4" (
    echo Abortado
    exit /b 0
) else (
    echo ❌ Opção inválida
    exit /b 1
)

echo.
pause
