"""Environment Selection Dialog - Escolher servidor (Local/Production)"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading


class EnvironmentDialog:
    """Dialog para escolher e configurar ambiente (Local ou Production)"""
    
    def __init__(self, parent):
        """Initialize environment selection dialog
        
        Args:
            parent: Parent window
        """
        self.parent = parent
        self.result = None
        self.dialog = None
        self.test_thread = None
        self.setup_dialog()
    
    def setup_dialog(self):
        """Setup the dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Selecionar Servidor DynamoDB")
        self.dialog.geometry("550x450")
        self.dialog.resizable(False, False)
        
        # Center dialog
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Label(
            header_frame,
            text="🗄️ Escolher Servidor DynamoDB",
            font=("Arial", 14, "bold")
        ).pack()
        
        ttk.Label(
            header_frame,
            text="Qual servidor você deseja usar?",
            font=("Arial", 10)
        ).pack(pady=(10, 0))
        
        # Separator
        ttk.Separator(self.dialog, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Main content frame
        content_frame = ttk.Frame(self.dialog)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Radio button variable
        self.env_var = tk.StringVar(value="local")
        
        # LOCAL OPTION
        self.setup_local_option(content_frame)
        
        # Separator
        ttk.Separator(self.dialog, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # PRODUCTION OPTION
        self.setup_production_option(content_frame)
        
        # Separator
        ttk.Separator(self.dialog, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=20, pady=15)
        
        self.connect_btn = ttk.Button(
            buttons_frame,
            text="✓ Conectar",
            command=self.on_connect
        )
        self.connect_btn.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="✕ Cancelar",
            command=self.on_cancel
        ).pack(side=tk.RIGHT, padx=5)
        
        # Test connection button (initially hidden)
        self.test_btn = ttk.Button(
            buttons_frame,
            text="🧪 Testar Conexão",
            command=self.test_connection,
            state=tk.DISABLED
        )
        self.test_btn.pack(side=tk.LEFT, padx=5)
    
    def setup_local_option(self, parent):
        """Setup local DynamoDB option"""
        # Frame
        local_frame = ttk.LabelFrame(parent, text="📱 DynamoDB Local", padding=15)
        local_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Radio button
        ttk.Radiobutton(
            local_frame,
            text="Usar DynamoDB Local (Desenvolvimento)",
            variable=self.env_var,
            value="local",
            command=self.on_env_changed
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Description
        description = ttk.Frame(local_frame)
        description.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        ttk.Label(
            description,
            text="✓ Sem custos",
            foreground="green",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        ttk.Label(
            description,
            text="✓ Rápido para desenvolvimento",
            foreground="green",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        ttk.Label(
            description,
            text="✓ Dados locais - não persistem",
            foreground="orange",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        # Configuration
        config_frame = ttk.LabelFrame(local_frame, text="⚙️ Configuração", padding=10)
        config_frame.pack(fill=tk.X, padx=0, pady=(10, 0))
        
        # Row 1: Protocol
        proto_frame = ttk.Frame(config_frame)
        proto_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(proto_frame, text="Protocolo:", width=15).pack(side=tk.LEFT)
        self.local_protocol = tk.StringVar(value="http")
        proto_combo = ttk.Combobox(
            proto_frame,
            textvariable=self.local_protocol,
            values=["http", "https"],
            width=20,
            state="readonly"
        )
        proto_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Row 2: Host
        host_frame = ttk.Frame(config_frame)
        host_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(host_frame, text="Host:", width=15).pack(side=tk.LEFT)
        self.local_host = tk.StringVar(value="localhost")
        ttk.Entry(host_frame, textvariable=self.local_host, width=23).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Row 3: Port
        port_frame = ttk.Frame(config_frame)
        port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(port_frame, text="Porta:", width=15).pack(side=tk.LEFT)
        self.local_port = tk.StringVar(value="8000")
        ttk.Entry(port_frame, textvariable=self.local_port, width=23).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Row 4: Full endpoint (display)
        endpoint_frame = ttk.Frame(config_frame)
        endpoint_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(endpoint_frame, text="Endpoint:", width=15).pack(side=tk.LEFT)
        
        self.local_endpoint_display = tk.StringVar(value="http://localhost:9000")
        ttk.Entry(
            endpoint_frame,
            textvariable=self.local_endpoint_display,
            width=23,
            state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Bind events para atualizar endpoint
        self.local_protocol.trace('w', self.update_local_endpoint)
        self.local_host.trace('w', self.update_local_endpoint)
        self.local_port.trace('w', self.update_local_endpoint)
    
    def setup_production_option(self, parent):
        """Setup production AWS option"""
        # Frame
        prod_frame = ttk.LabelFrame(parent, text="☁️ AWS Cloud (Produção)", padding=15)
        prod_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Radio button
        ttk.Radiobutton(
            prod_frame,
            text="Usar AWS DynamoDB (Produção)",
            variable=self.env_var,
            value="production",
            command=self.on_env_changed
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Description
        description = ttk.Frame(prod_frame)
        description.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        ttk.Label(
            description,
            text="✓ Dados persistentes",
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
        
        # Configuration
        config_frame = ttk.LabelFrame(prod_frame, text="⚙️ Configuração", padding=10)
        config_frame.pack(fill=tk.X, padx=0, pady=(10, 0))
        
        # Região
        region_frame = ttk.Frame(config_frame)
        region_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(region_frame, text="Região AWS:", width=15).pack(side=tk.LEFT)
        
        self.aws_region = tk.StringVar(value="us-east-1")
        region_combo = ttk.Combobox(
            region_frame,
            textvariable=self.aws_region,
            values=[
                "us-east-1",
                "us-east-2",
                "us-west-1",
                "us-west-2",
                "ca-central-1",
                "eu-west-1",
                "eu-west-2",
                "eu-central-1",
                "ap-northeast-1",
                "ap-northeast-2",
                "ap-southeast-1",
                "ap-southeast-2",
                "sa-east-1",
            ],
            width=20,
            state="readonly"
        )
        region_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    
    def update_local_endpoint(self, *args):
        """Update the display of local endpoint"""
        protocol = self.local_protocol.get()
        host = self.local_host.get()
        port = self.local_port.get()
        
        endpoint = f"{protocol}://{host}:{port}"
        self.local_endpoint_display.set(endpoint)
    
    def on_env_changed(self):
        """Handle environment selection change"""
        selected = self.env_var.get()
        
        # Enable/disable test button based on selection
        if selected == "local":
            self.test_btn.config(state=tk.NORMAL)
        else:
            self.test_btn.config(state=tk.DISABLED)
    
    def test_connection(self):
        """Test connection to local DynamoDB"""
        endpoint = self.local_endpoint_display.get()
        
        self.connect_btn.config(state=tk.DISABLED)
        self.test_btn.config(state=tk.DISABLED, text="🧪 Testando...")
        
        # Run test in background thread
        def test():
            try:
                import requests
                response = requests.head(endpoint, timeout=5)
                
                self.dialog.after(0, lambda: messagebox.showinfo(
                    "Sucesso",
                    f"✓ Conexão bem-sucedida!\n\n"
                    f"Endpoint: {endpoint}\n"
                    f"Status: {response.status_code}"
                ))
            except ImportError:
                # requests não instalado, tentar com urllib
                try:
                    import urllib.request
                    urllib.request.urlopen(endpoint, timeout=5)
                    
                    self.dialog.after(0, lambda: messagebox.showinfo(
                        "Sucesso",
                        f"✓ Conexão bem-sucedida!\n\n"
                        f"Endpoint: {endpoint}"
                    ))
                except Exception as e:
                    self.dialog.after(0, lambda: messagebox.showerror(
                        "Erro de Conexão",
                        f"✗ Não foi possível conectar a:\n{endpoint}\n\n"
                        f"Erro: {str(e)}\n\n"
                        f"Certifique-se de que o DynamoDB Local está rodando."
                    ))
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror(
                    "Erro de Conexão",
                    f"✗ Não foi possível conectar a:\n{endpoint}\n\n"
                    f"Erro: {str(e)}\n\n"
                    f"Certifique-se de que o DynamoDB Local está rodando."
                ))
            finally:
                self.dialog.after(0, lambda: self.connect_btn.config(state=tk.NORMAL))
                self.dialog.after(0, lambda: self.test_btn.config(state=tk.NORMAL, text="🧪 Testar Conexão"))
        
        self.test_thread = threading.Thread(target=test, daemon=True)
        self.test_thread.start()
    
    def on_connect(self):
        """Handle connect button"""
        selected_env = self.env_var.get()
        
        if selected_env == "local":
            endpoint = self.local_endpoint_display.get()
            
            # Validar endpoint
            if not endpoint or not endpoint.startswith(('http://', 'https://')):
                messagebox.showerror("Erro", "Endpoint inválido!")
                return
            
            self.result = {
                'type': 'local',
                'endpoint': endpoint
            }
        else:
            region = self.aws_region.get()
            
            if not region:
                messagebox.showerror("Erro", "Selecione uma região!")
                return
            
            self.result = {
                'type': 'production',
                'region': region
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
