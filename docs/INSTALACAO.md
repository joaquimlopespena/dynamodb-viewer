# Instalação do DynamoDB Viewer no Linux

Há duas formas de instalar/executar a aplicação no Linux.

---

## 1. Instalação via pip (recomendado para desenvolvimento)

Requer Python 3.10+ e pip.

### Opção A: Instalar a partir do código-fonte (editable)

```bash
cd dynamodb-viewer
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Depois, execute em qualquer pasta:

```bash
dynamodb-viewer
```

### Opção B: Instalar a partir do wheel (pacote gerado)

```bash
# Gerar o wheel
cd dynamodb-viewer
pip install build
python3 -m build --wheel --outdir dist

# Instalar o wheel em outro ambiente
pip install dist/dynamodb_viewer-*.whl
dynamodb-viewer
```

### Opção C: Instalar com pipx (isolado, sem ativar venv)

```bash
pipx install /caminho/para/dynamodb-viewer
dynamodb-viewer
```

---

## 2. Executável standalone (PyInstaller)

Gera um único executável que não exige Python instalado na máquina.

### Pré-requisitos

- Python 3.10+
- PyInstaller: `pip install pyinstaller`

### Gerar o executável

```bash
cd dynamodb-viewer
# Use o venv do projeto (recomendado) ou pip install pyinstaller no seu ambiente
.venv/bin/python -m pip install pyinstaller
.venv/bin/python -m PyInstaller dynamodb_viewer.spec
```

Se não tiver venv: `python3 -m pip install --user pyinstaller` e depois `python3 -m PyInstaller dynamodb_viewer.spec`.

O executável será criado em:

- `dist/dynamodb-viewer`

### Executar

```bash
./dist/dynamodb-viewer
```

### Script de build (wheel + executável)

```bash
chmod +x build_linux.sh
./build_linux.sh pip          # só gera o wheel em dist/
./build_linux.sh pyinstaller # só gera o executável
./build_linux.sh all         # gera wheel e executável
```

---

## Resumo

| Método              | Comando / resultado              | Uso típico                    |
|---------------------|----------------------------------|-------------------------------|
| pip install -e .    | `dynamodb-viewer` no PATH       | Desenvolvimento               |
| pip install *.whl  | `dynamodb-viewer` no PATH       | Instalação em outro ambiente |
| PyInstaller        | `./dist/dynamodb-viewer`        | Distribuição sem Python      |

---

## Dependências (incluídas no pacote)

- boto3
- tqdm
- ijson

O Tkinter (GUI) faz parte da biblioteca padrão do Python; em alguns sistemas pode ser necessário instalar o pacote do sistema, por exemplo:

- **Debian/Ubuntu:** `sudo apt install python3-tk`
- **Fedora:** `sudo dnf install python3-tkinter`
