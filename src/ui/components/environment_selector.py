"""Environment Selector Dialog"""

import os
import customtkinter as ctk
from tkinter import messagebox

from src.utils.resource_paths import get_logo_path, load_icon_for_ctk


class EnvironmentSelector:
    """Dialog to select DynamoDB environment"""

    def __init__(self, root):
        self.root = root
        self.root.title("DynamoDB Viewer - Selecionar Servidor")
        self.root.geometry("520x580")
        self.root.resizable(False, False)
        self.result = None

        # Ícone da janela
        load_icon_for_ctk(self.root)

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (260)
        y = (self.root.winfo_screenheight() // 2) - (290)
        self.root.geometry(f"+{x}+{y}")

        self.setup_ui()

    def _load_logo_small(self, max_height=72):
        """Carrega o logo redimensionado. Retorna CTkImage ou None."""
        logo_path = get_logo_path()
        if not os.path.isfile(logo_path):
            return None
        try:
            from PIL import Image
            img = Image.open(logo_path)
            w, h = img.size
            if h > max_height:
                ratio = max_height / h
                new_w = int(w * ratio)
                img = img.resize((new_w, max_height), Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        except Exception:
            return None

    def setup_ui(self):
        """Setup UI"""
        # Main container
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Logo no topo
        self._logo_img = self._load_logo_small(max_height=72)
        if self._logo_img is not None:
            logo_label = ctk.CTkLabel(main_container, image=self._logo_img, text="")
            logo_label.pack(pady=(0, 10))

        # Title
        title = ctk.CTkLabel(
            main_container,
            text="Selecionar Servidor DynamoDB",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(0, 20))

        # Mode variable
        self.mode_var = ctk.StringVar(value="local")

        # Option 1: Local
        local_frame = ctk.CTkFrame(main_container)
        local_frame.pack(fill="x", pady=10)

        local_header = ctk.CTkFrame(local_frame, fg_color="transparent")
        local_header.pack(fill="x", padx=15, pady=(15, 5))

        self.local_radio = ctk.CTkRadioButton(
            local_header,
            text="DynamoDB Local",
            variable=self.mode_var,
            value="local",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.local_radio.pack(anchor="w")

        local_content = ctk.CTkFrame(local_frame, fg_color="transparent")
        local_content.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            local_content,
            text="Endpoint:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 2))

        self.local_endpoint = ctk.StringVar(value="http://localhost:9000")
        endpoint_entry = ctk.CTkEntry(
            local_content,
            textvariable=self.local_endpoint,
            width=400,
            height=35
        )
        endpoint_entry.pack(anchor="w", fill="x")

        ctk.CTkLabel(
            local_content,
            text="Sem custos • Desenvolvimento",
            font=ctk.CTkFont(size=11),
            text_color="#4CAF50"
        ).pack(anchor="w", pady=(5, 0))

        # Option 2: Production
        prod_frame = ctk.CTkFrame(main_container)
        prod_frame.pack(fill="x", pady=10)

        prod_header = ctk.CTkFrame(prod_frame, fg_color="transparent")
        prod_header.pack(fill="x", padx=15, pady=(15, 5))

        self.prod_radio = ctk.CTkRadioButton(
            prod_header,
            text="AWS DynamoDB (Produção)",
            variable=self.mode_var,
            value="production",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.prod_radio.pack(anchor="w")

        prod_content = ctk.CTkFrame(prod_frame, fg_color="transparent")
        prod_content.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            prod_content,
            text="Região AWS:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 2))

        self.aws_region = ctk.StringVar(value="us-east-1")
        region_combo = ctk.CTkComboBox(
            prod_content,
            variable=self.aws_region,
            values=[
                "us-east-1", "us-east-2", "us-west-1", "us-west-2",
                "eu-west-1", "eu-central-1", "ap-northeast-1", "ap-southeast-1"
            ],
            width=400,
            height=35,
            state="readonly"
        )
        region_combo.pack(anchor="w", fill="x")

        ctk.CTkLabel(
            prod_content,
            text="⚠️ Requer AWS CLI configurado (aws configure)",
            font=ctk.CTkFont(size=11),
            text_color="#FFA726"
        ).pack(anchor="w", pady=(5, 0))

        # Buttons frame
        btn_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=self.on_cancel,
            width=120,
            height=40,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            btn_frame,
            text="Conectar",
            command=self.on_connect,
            width=120,
            height=40
        ).pack(side="right")

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
