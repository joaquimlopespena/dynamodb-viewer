#!/bin/bash
# Script de instalação do DynamoDB Viewer

echo "🗄️  DynamoDB Viewer - Setup"
echo "=========================="
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.6 ou superior."
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Verifica AWS CLI
if ! command -v aws &> /dev/null; then
    echo "⚠️  AWS CLI não encontrado."
    echo ""
    echo "Instale o AWS CLI:"
    echo "  Linux: curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o awscliv2.zip && unzip awscliv2.zip && sudo ./aws/install"
    echo "  macOS: brew install awscli"
    echo "  Windows: https://aws.amazon.com/cli/"
    echo ""
    read -p "Deseja continuar sem AWS CLI? (s/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
else
    echo "✅ AWS CLI encontrado: $(aws --version)"
fi

# Instala dependências
echo ""
echo "📦 Instalando dependências Python..."
pip3 install -r requirements.txt --break-system-packages

if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas com sucesso!"
else
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

# Verifica configuração AWS
echo ""
if command -v aws &> /dev/null; then
    echo "🔑 Verificando configuração AWS..."
    
    if aws configure get aws_access_key_id &> /dev/null; then
        echo "✅ AWS CLI já configurado!"
    else
        echo "⚠️  AWS CLI não configurado."
        echo ""
        read -p "Deseja configurar agora? (s/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            aws configure
        fi
    fi
fi

# Torna o script executável
chmod +x dynamodb_viewer.py

echo ""
echo "✅ Setup concluído!"
echo ""
echo "Para iniciar o aplicativo, execute:"
echo "  python3 dynamodb_viewer.py"
echo ""
echo "Ou crie um alias no seu .bashrc/.zshrc:"
echo "  alias dynamodb-viewer='python3 $(pwd)/dynamodb_viewer.py'"
