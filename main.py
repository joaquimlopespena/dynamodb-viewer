#!/usr/bin/env python3
"""
DynamoDB Viewer - Interface de Filtros Visuais
Similar à interface AWS Console
"""
import sys
import os

# Suporte a PyInstaller (executável empacotado)
if getattr(sys, "frozen", False):
    sys.path.insert(0, sys._MEIPASS)

import customtkinter as ctk
from src.ui.windows import MainWindow
from src.ui.components.environment_selector import EnvironmentSelector
from src.config import config

# Configurar tema do CustomTkinter
ctk.set_appearance_mode("dark")  # "dark", "light", ou "system"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"


def main():
    """Main entry point"""
    # Show environment selector
    root = ctk.CTk()
    selector = EnvironmentSelector(root)
    root.mainloop()

    if selector.result is None:
        return

    mode, value = selector.result

    # Configure based on selection
    if mode == "local":
        config.set_local(value)
    else:
        config.set_production(value)

    # Print configuration
    config.print_config()

    # Create main application window
    app_root = ctk.CTk()
    app = MainWindow(app_root)
    app_root.mainloop()


if __name__ == "__main__":
    main()
