@echo off
REM Quick Launch Script - DynamoDB Viewer (Windows)
REM Opções rápidas de inicialização

setlocal enabledelayedexpansion

if "%1%"=="" (
    REM Default: Local (fastest)
    python main.py
) else if "%1%"=="local" or "%1%"=="-l" (
    REM Local mode
    set endpoint=%2
    if "%endpoint%"=="" set endpoint=http://localhost:9000
    python main.py --local !endpoint!
) else if "%1%"=="prod" or "%1%"=="-p" (
    REM Production mode
    set region=%2
    if "%region%"=="" set region=us-east-1
    python main.py --production !region!
) else if "%1%"=="dialog" or "%1%"=="-d" (
    REM Show connection dialog
    python main.py --dialog
) else if "%1%"=="help" or "%1%"=="-h" (
    echo DynamoDB Viewer - Usage
    echo.
    echo Usage: %0 [command] [args]
    echo.
    echo Commands:
    echo   (none)           Start in Local mode (default, fastest^)
    echo   local [endpoint] Start in Local mode with custom endpoint
    echo   prod [region]    Start in Production mode (AWS^)
    echo   dialog           Show connection dialog on startup
    echo   help             Show this help message
    echo.
    echo Examples:
    echo   launch.bat                    REM Start local (fastest^)
    echo   launch.bat local              REM Start local (default endpoint^)
    echo   launch.bat local http://localhost:8001
    echo   launch.bat prod eu-west-1    REM Start AWS EU region
    echo   launch.bat dialog             REM Show connection dialog
    echo.
) else (
    echo Unknown command: %1
    echo Use: %0 help
    exit /b 1
)

endlocal
