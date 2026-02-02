#!/bin/bash
"""
Setup script for DynamoDB Local

This script helps you set up DynamoDB Local for development.
"""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     DynamoDB Viewer - Setup para DynamoDB Local            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado!"
    echo ""
    echo "Por favor, instale Docker em:"
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✓ Docker encontrado"
echo ""

# Check if DynamoDB Local image exists
if ! docker image inspect localstack/localstack:latest &> /dev/null 2>&1; then
    echo "📥 Baixando imagem DynamoDB Local..."
    docker pull amazon/dynamodb-local:latest || {
        echo "❌ Erro ao baixar a imagem"
        exit 1
    }
    echo "✓ Imagem baixada com sucesso"
else
    echo "✓ Imagem DynamoDB Local já está instalada"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ OPÇÕES DE INICIALIZAÇÃO                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "1) Iniciar DynamoDB Local em container Docker"
echo "2) Parar DynamoDB Local"
echo "3) Ver logs do container"
echo "4) Voltar"
echo ""
read -p "Escolha uma opção (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Iniciando DynamoDB Local..."
        docker run -d \
            --name dynamodb-local \
            -p 8000:8000 \
            amazon/dynamodb-local:latest
        
        if [ $? -eq 0 ]; then
            echo "✓ DynamoDB Local iniciado com sucesso!"
            echo ""
            echo "Endpoint: http://localhost:9000"
            echo ""
            echo "Aguardando inicialização..."
            sleep 3
            
            # Try to connect
            if curl -s http://localhost:9000/ > /dev/null; then
                echo "✓ Conectado ao DynamoDB Local!"
                echo ""
                echo "Você pode agora executar:"
                echo "  $ python main.py"
            else
                echo "⚠️ Aguarde alguns segundos e tente novamente"
            fi
        else
            echo "❌ Erro ao iniciar container"
            echo "Talvez já exista um container com esse nome"
            echo "Tente: docker rm dynamodb-local"
        fi
        ;;
    
    2)
        echo ""
        echo "Parando DynamoDB Local..."
        docker stop dynamodb-local
        docker rm dynamodb-local
        echo "✓ DynamoDB Local parado"
        ;;
    
    3)
        echo ""
        echo "Logs do DynamoDB Local:"
        echo "========================"
        docker logs -f dynamodb-local
        ;;
    
    4)
        echo "Abortado"
        exit 0
        ;;
    
    *)
        echo "❌ Opção inválida"
        exit 1
        ;;
esac

echo ""
