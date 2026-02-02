#!/bin/bash
"""
Quick Launch Script - DynamoDB Viewer
Opções rápidas de inicialização
"""

if [ "$1" = "" ]; then
    # Default: Local (fastest)
    python main.py
elif [ "$1" = "local" ] || [ "$1" = "-l" ]; then
    # Local mode
    endpoint="${2:-http://localhost:9000}"
    python main.py --local "$endpoint"
elif [ "$1" = "prod" ] || [ "$1" = "-p" ]; then
    # Production mode
    region="${2:-us-east-1}"
    python main.py --production "$region"
elif [ "$1" = "dialog" ] || [ "$1" = "-d" ]; then
    # Show connection dialog
    python main.py --dialog
elif [ "$1" = "help" ] || [ "$1" = "-h" ]; then
    echo "DynamoDB Viewer - Usage"
    echo ""
    echo "Usage: $0 [command] [args]"
    echo ""
    echo "Commands:"
    echo "  (none)           Start in Local mode (default, fastest)"
    echo "  local [endpoint] Start in Local mode with custom endpoint"
    echo "  prod [region]    Start in Production mode (AWS)"
    echo "  dialog           Show connection dialog on startup"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./launch.sh                    # Start local (fastest)"
    echo "  ./launch.sh local              # Start local (default endpoint)"
    echo "  ./launch.sh local http://localhost:8001  # Custom endpoint"
    echo "  ./launch.sh prod eu-west-1    # Start AWS EU region"
    echo "  ./launch.sh dialog             # Show connection dialog"
    echo ""
else
    echo "Unknown command: $1"
    echo "Use: $0 help"
    exit 1
fi
