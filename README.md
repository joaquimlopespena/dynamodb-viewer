# DynamoDB Viewer

Aplicativo desktop em Python para visualizar e gerenciar dados do Amazon DynamoDB (AWS e DynamoDB Local).

## Instalação no Linux

- **Via pip (pacote):**  
  `pip install -e .` na pasta do projeto e depois execute `dynamodb-viewer`.

- **Executável standalone:**  
  Use PyInstaller: `pyinstaller dynamodb_viewer.spec`. O executável fica em `dist/dynamodb-viewer`.

- **Detalhes:**  
  Veja [docs/INSTALACAO.md](docs/INSTALACAO.md) para todas as opções (pip, wheel, pipx, PyInstaller e script `build_linux.sh`).

## Pré-requisitos

- Python 3.10+
- Tkinter (ex.: `sudo apt install python3-tk` em Ubuntu/Debian)
- boto3, tqdm, ijson (instalados automaticamente pelo pip)

## Documentação

- [docs/README.md](docs/README.md) — visão geral e funcionalidades  
- [docs/INSTALACAO.md](docs/INSTALACAO.md) — instalação e build para Linux
