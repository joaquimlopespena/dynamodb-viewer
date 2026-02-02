"""Connection Dialog - Escolher ambiente de conexão"""

import tkinter as tk
from tkinter import ttk, messagebox
import os


class ConnectionDialog:
    """Dialog para escolher entre DynamoDB Local ou AWS Cloud"""
    
    def __init__(self, parent):
        """Initialize connection dialog
        
        Args:
            parent: Parent window
        """
        self.parent = parent
        self.result = None
        self.dialog = None
        self.setup_dialog()
    
    def setup_dialog(self):
        """Setup the dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Selecionar Ambiente DynamoDB")
        self.dialog.geometry("500x350")
        self.dialog.resizable(False, False)
        
        # Center dialog
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(
            header_frame,
            text="🗄️ DynamoDB Viewer - Selecionar Ambiente",
            font=("Arial", 14, "bold")
        ).pack()
        
        ttk.Label(
            header_frame,
            text="Escolha onde deseja conectar:",
            font=("Arial", 10)
        ).pack(pady=(10, 0))
        
        # Separator
        ttk.Separator(self.dialog, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Options frame
        options_frame = ttk.Frame(self.dialog)
        options_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Option 1: Local
        self.setup_local_option(options_frame)
        
        # Option 2: Production
        self.setup_production_option(options_frame)
        
        # Separator
        ttk.Separator(self.dialog, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Button(
            buttons_frame,
            text="Conectar",
            command=self.on_connect
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Cancelar",
            command=self.on_cancel
        ).pack(side=tk.RIGHT, padx=5)
    
    def setup_local_option(self, parent):
        """Setup local DynamoDB option"""
        # Frame
        local_frame = ttk.LabelFrame(parent, text="📱 DynamoDB Local", padding=15)
        local_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Radio button
        self.env_var = tk.StringVar(value="local")
        
        ttk.Radiobutton(
            local_frame,
            text="Conectar ao DynamoDB Local",
            variable=self.env_var,
            value="local"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Description
        description = ttk.Frame(local_frame)
        description.pack(fill=tk.X, padx=20)
        
        ttk.Label(
            description,
            text="✓ Desenvolvimento sem custos",
            foreground="green",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        ttk.Label(
            description,
            text="✓ Executando em http://localhost:9000",
            foreground="green",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        ttk.Label(
            description,
            text="✓ Dados apenas durante a sessão",
            foreground="orange",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        # Endpoint config
        config_frame = ttk.Frame(local_frame)
        config_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        ttk.Label(config_frame, text="Endpoint:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.local_endpoint = tk.StringVar(value="http://localhost:9000")
        ttk.Entry(
            config_frame,
            textvariable=self.local_endpoint,
            width=30
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def setup_production_option(self, parent):
        """Setup production AWS option"""
        # Frame
        prod_frame = ttk.LabelFrame(parent, text="☁️ AWS Cloud (Produção)", padding=15)
        prod_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Radio button
        ttk.Radiobutton(
            prod_frame,
            text="Conectar ao AWS DynamoDB",
            variable=self.env_var,
            value="production"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Description
        description = ttk.Frame(prod_frame)
        description.pack(fill=tk.X, padx=20)
        
        ttk.Label(
            description,
            text="✓ Dados persistentes em produção",
            foreground="green",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        ttk.Label(
            description,
            text="✓ Acesso a dados reais",
            foreground="green",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        ttk.Label(
            description,
            text="⚠ Requer AWS CLI configurado (aws configure)",
            foreground="orange",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        # Region config
        config_frame = ttk.Frame(prod_frame)
        config_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        ttk.Label(config_frame, text="Região AWS:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.aws_region = tk.StringVar(value="us-east-1")
        region_combo = ttk.Combobox(
            config_frame,
            textvariable=self.aws_region,
            values=[
                "us-east-1",
                "us-east-2",
                "us-west-1",
                "us-west-2",
                "eu-west-1",
                "eu-central-1",
                "ap-northeast-1",
                "ap-southeast-1",
            ],
            width=27,
            state="readonly"
        )
        region_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def on_connect(self):
        """Handle connect button"""
        selected_env = self.env_var.get()
        
        if selected_env == "local":
            self.result = {
                'type': 'local',
                'endpoint': self.local_endpoint.get(),
                'region': 'us-east-1'
            }
        else:
            self.result = {
                'type': 'production',
                'region': self.aws_region.get()
            }
        
        self.dialog.destroy()
        self.parent.destroy()
    
    def on_cancel(self):
        """Handle cancel button"""
        self.result = None
        self.dialog.destroy()
        self.parent.destroy()
    
    def show(self):
        """Show dialog and wait for result
        
        Returns:
            dict: Selected configuration or None if cancelled
        """
        self.parent.wait_window(self.dialog)
        return self.result
