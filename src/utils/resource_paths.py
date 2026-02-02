"""Caminhos de recursos (imagens, etc.) que funcionam com código-fonte e com binário PyInstaller."""

import os
import sys


def get_base_path():
    """Diretório base do app: projeto quando em desenvolvimento, sys._MEIPASS quando empacotado."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    # Código-fonte: raiz do projeto (pasta que contém main.py)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_logo_path():
    """Caminho absoluto para img/logo.png."""
    return os.path.join(get_base_path(), "img", "logo.png")


def load_icon_for_tk(root):
    """
    Carrega logo.png como ícone da janela Tk.
    Mantém referência no root para não ser coletado pelo GC.
    Retorna True se o ícone foi definido, False caso contrário.
    """
    path = get_logo_path()
    if not os.path.isfile(path):
        return False
    # Tentar Pillow primeiro (PNG costuma funcionar melhor)
    try:
        from PIL import Image, ImageTk
        img = Image.open(path).convert("RGBA")
        # Ícone pequeno para a barra de título (32x32 ou menor)
        resample = getattr(Image, "Resampling", Image).LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        img.thumbnail((32, 32), resample)
        photo = ImageTk.PhotoImage(img)
        root.iconphoto(True, photo)
        if not hasattr(root, "_icon_photo"):
            root._icon_photo = photo
        return True
    except Exception:
        pass
    try:
        from tkinter import PhotoImage
        img = PhotoImage(file=path)
        root.iconphoto(True, img)
        if not hasattr(root, "_icon_photo"):
            root._icon_photo = img
        return True
    except Exception:
        return False
