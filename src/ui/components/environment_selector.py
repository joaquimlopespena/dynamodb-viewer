"""Environment Selector Dialog"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

from src.utils.resource_paths import get_logo_path, load_icon_for_tk


class EnvironmentSelector:
    """Dialog to select DynamoDB environment"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DynamoDB Viewer - Selecionar Servidor")
        self.root.geometry("520x560")
        self.root.resizable(False, False)
        self.result = None
        
        # Ícone da janela (logo da aplicação)
        load_icon_for_tk(self.root)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def _load_logo_small(self, max_height=72):
        """Carrega o logo redimensionado para caber no topo da janela. Retorna PhotoImage ou None."""
        logo_path = get_logo_path()
        if not os.path.isfile(logo_path):
            return None
        try:
            from tkinter import PhotoImage
            full = PhotoImage(file=logo_path)
            w, h = full.width(), full.height()
            if h <= max_height:
                return full
            # Reduzir com subsample para altura máxima max_height
            factor = max(2, (h + max_height - 1) // max_height)
            small = full.subsample(factor, factor)
            return small
        except Exception:
            return None
    
    def setup_ui(self):
        """Setup UI"""
        # Logo no topo (redimensionado para não dominar a tela)
        self._logo_img = self._load_logo_small(max_height=72)
        if self._logo_img is not None:
            logo_label = ttk.Label(self.root, image=self._logo_img)
            logo_label.pack(pady=(12, 4))
        
        # Title
        title = ttk.Label(self.root, text="🗄️ Selecionar Servidor DynamoDB", 
                         font=("Arial", 14, "bold"))
        title.pack(pady=6)
        
        # Main frame (não expandir demais para o conteúdo ficar visível)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.X, padx=15, pady=8)
        
        # Option 1: Local
        local_frame = ttk.LabelFrame(main_frame, text="📱 DynamoDB Local", padding=12)
        local_frame.pack(fill=tk.X, pady=8)
        
        self.mode_var = tk.StringVar(value="local")
        ttk.Radiobutton(local_frame, text="Servidor Local", variable=self.mode_var, 
                       value="local", command=self.on_mode_change).pack(anchor=tk.W)
        
        ttk.Label(local_frame, text="Endpoint:", font=("Arial", 9)).pack(anchor=tk.W, pady=(8, 3))
        self.local_endpoint = tk.StringVar(value="http://localhost:9000")
        endpoint_entry = ttk.Entry(local_frame, textvariable=self.local_endpoint, width=50)
        endpoint_entry.pack(anchor=tk.W, fill=tk.X)
        ttk.Label(local_frame, text="Sem custos • Desenvolvimento", 
                 font=("Arial", 8), foreground="green").pack(anchor=tk.W, pady=(2, 0))
        
        # Option 2: Production
        prod_frame = ttk.LabelFrame(main_frame, text="☁️ AWS DynamoDB (Produção)", padding=12)
        prod_frame.pack(fill=tk.X, pady=8)
        
        ttk.Radiobutton(prod_frame, text="Servidor AWS", variable=self.mode_var, 
                       value="production", command=self.on_mode_change).pack(anchor=tk.W)
        
        ttk.Label(prod_frame, text="Região AWS:", font=("Arial", 9)).pack(anchor=tk.W, pady=(8, 3))
        self.aws_region = tk.StringVar(value="us-east-1")
        region_combo = ttk.Combobox(prod_frame, textvariable=self.aws_region,
                    values=["us-east-1", "us-east-2", "us-west-1", "us-west-2", 
                           "eu-west-1", "eu-central-1", "ap-northeast-1", "ap-southeast-1"],
                    width=48, state="readonly")
        region_combo.pack(anchor=tk.W, fill=tk.X)
        ttk.Label(prod_frame, text="⚠️ Requer AWS CLI configurado (aws configure)", 
                 font=("Arial", 8), foreground="orange").pack(anchor=tk.W, pady=(2, 0))
        
        # Buttons frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Button(btn_frame, text="Conectar", command=self.on_connect, width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.on_cancel, width=15).pack(side=tk.RIGHT, padx=5)
    
    def on_mode_change(self):
        """Handle mode change"""
        pass
    
    def on_connect(self):
        """Connect with selected settings"""
        if self.mode_var.get() == "local":
            endpoint = self.local_endpoint.get().strip()
            if not endpoint:
                messagebox.showerror("Erro", "Digite um endpoint válido")
                return
            self.result = ("local", endpoint)
        else:
            self.result = ("production", self.aws_region.get())
        
        self.root.destroy()
    
    def on_cancel(self):
        """Cancel and close"""
        self.result = None
        self.root.destroy()
