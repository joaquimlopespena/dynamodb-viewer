"""Import Dialog Component"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from src.config import config


class ImportDialog:
    """Dialog for importing data from JSON files to DynamoDB Local"""

    def __init__(self, parent, db_service, table_name=None):
        """Initialize import dialog

        Args:
            parent: Parent window
            db_service: DynamoDBService instance
            table_name: Optional table name to import to
        """
        self.parent = parent
        self.db_service = db_service
        self.table_name = table_name
        self.result = None

        # Verificar se está em modo local
        if not config.DYNAMODB_LOCAL:
            messagebox.showerror(
                "Erro de Segurança",
                "❌ Importação só é permitida em modo LOCAL!\n\n"
                "Por segurança, esta funcionalidade não funciona quando conectado à produção."
            )
            return

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Importar Dados - DynamoDB Local")
        self.dialog.geometry("700x750")
        self.dialog.resizable(True, True)

        # Aguardar janela ficar visível antes de configurar
        self.dialog.after(100, self._finish_init)

    def _finish_init(self):
        """Finaliza inicialização após janela estar visível"""
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center window
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350)
        y = (self.dialog.winfo_screenheight() // 2) - (375)
        self.dialog.geometry(f"+{x}+{y}")

        self.setup_ui()

    def setup_ui(self):
        """Setup UI components"""
        # Main scrollable container
        main_container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        ctk.CTkLabel(
            main_container,
            text="📥 Importar Dados para DynamoDB Local",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 15))

        # Security warning frame
        warning_frame = ctk.CTkFrame(main_container)
        warning_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            warning_frame,
            text="🔒 Segurança",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        warning_text = (
            "✓ Modo LOCAL ativo\n"
            "✓ Conexão com produção DESABILITADA\n"
            "✓ Dados serão importados apenas para o DynamoDB local"
        )
        ctk.CTkLabel(
            warning_frame,
            text=warning_text,
            font=ctk.CTkFont(size=11),
            text_color="#4CAF50",
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # Table selection frame
        table_frame = ctk.CTkFrame(main_container)
        table_frame.pack(fill="both", expand=True, pady=5)

        ctk.CTkLabel(
            table_frame,
            text="Tabela de Destino",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Table name input row
        input_row = ctk.CTkFrame(table_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(input_row, text="Tabela:").pack(side="left", padx=(0, 5))

        self.table_var = ctk.StringVar(value=self.table_name or "")
        table_entry = ctk.CTkEntry(
            input_row,
            textvariable=self.table_var,
            width=350,
            height=32
        )
        table_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            input_row,
            text="🔄 Atualizar",
            command=self.load_tables,
            width=100,
            height=32
        ).pack(side="left")

        # Table list
        ctk.CTkLabel(
            table_frame,
            text="Lista de tabelas disponíveis:",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Scrollable frame for table list
        self.tables_scrollable = ctk.CTkScrollableFrame(table_frame, height=120)
        self.tables_scrollable.pack(fill="x", padx=15, pady=(0, 10))

        self.table_buttons = []
        self.load_tables()

        # File selection frame
        file_frame = ctk.CTkFrame(main_container)
        file_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            file_frame,
            text="Arquivo JSON",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        file_row = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_row.pack(fill="x", padx=15, pady=5)

        self.file_var = ctk.StringVar(value="")
        file_entry = ctk.CTkEntry(
            file_row,
            textvariable=self.file_var,
            width=400,
            height=32
        )
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            file_row,
            text="📁 Selecionar Arquivo",
            command=self.select_file,
            width=150,
            height=32
        ).pack(side="left")

        ctk.CTkLabel(
            file_frame,
            text="💡 Dica: Digite o caminho do arquivo ou use o botão para navegar",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(anchor="w", padx=15, pady=(5, 10))

        # Progress frame
        progress_frame = ctk.CTkFrame(main_container)
        progress_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            progress_frame,
            text="Progresso",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.progress_var = ctk.StringVar(value="Aguardando início...")
        ctk.CTkLabel(
            progress_frame,
            textvariable=self.progress_var,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=15, pady=2)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=600)
        self.progress_bar.pack(fill="x", padx=15, pady=(5, 10))
        self.progress_bar.set(0)

        # Log frame
        log_frame = ctk.CTkFrame(main_container)
        log_frame.pack(fill="both", expand=True, pady=5)

        ctk.CTkLabel(
            log_frame,
            text="Log",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=150,
            font=ctk.CTkFont(family="Courier", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self.log_text.insert("0.0", "📋 Pronto para importar. Selecione o arquivo e clique em 'Importar'.\n")
        self.log_text.configure(state="disabled")

        # Buttons frame
        btn_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        self.import_btn = ctk.CTkButton(
            btn_frame,
            text="▶ Importar",
            command=self.start_import,
            width=120,
            height=40,
            fg_color="#2d5a27",
            hover_color="#3d7a37"
        )
        self.import_btn.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=self.dialog.destroy,
            width=120,
            height=40,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        ).pack(side="right", padx=5)

    def select_file(self):
        """Open file dialog to select JSON file"""
        current_path = self.file_var.get().strip()
        if current_path and os.path.exists(current_path):
            default_dir = os.path.dirname(current_path)
        elif current_path and os.path.dirname(current_path):
            default_dir = os.path.dirname(current_path)
        else:
            default_dir = "/home/joaquim/dumps/DynamoDB"
            if not os.path.exists(default_dir):
                possible_dirs = [
                    os.path.expanduser("~/dumps/DynamoDB"),
                    os.path.expanduser("~/Downloads"),
                    os.path.expanduser("~")
                ]
                for d in possible_dirs:
                    if os.path.exists(d):
                        default_dir = d
                        break
                else:
                    default_dir = os.path.expanduser("~")

        filename = filedialog.askopenfilename(
            title="Selecionar arquivo JSON",
            filetypes=[
                ("JSON files", "*.json"),
                ("Todos os arquivos", "*.*"),
            ],
            initialdir=default_dir,
            initialfile=""
        )

        if filename:
            self.file_var.set(filename)
            self.log(f"Arquivo selecionado: {os.path.basename(filename)}")

    def load_tables(self):
        """Load list of tables from DynamoDB"""
        try:
            # Clear existing buttons
            for btn in self.table_buttons:
                btn.destroy()
            self.table_buttons = []

            tables = self.db_service.get_tables()

            if tables:
                for table in tables:
                    btn = ctk.CTkButton(
                        self.tables_scrollable,
                        text=table,
                        command=lambda t=table: self.on_table_select(t),
                        height=28,
                        anchor="w",
                        fg_color="transparent",
                        text_color=("gray10", "gray90"),
                        hover_color=("gray70", "gray30")
                    )
                    btn.pack(fill="x", pady=1)
                    self.table_buttons.append(btn)

                    # Highlight pre-selected table
                    if table == self.table_var.get():
                        btn.configure(fg_color=("gray75", "gray25"))
            else:
                ctk.CTkLabel(
                    self.tables_scrollable,
                    text="(Nenhuma tabela encontrada)",
                    text_color="gray"
                ).pack(anchor="w")
                self.log("ℹ️ Nenhuma tabela encontrada.")

        except Exception as e:
            self.log(f"⚠️ Erro ao carregar tabelas: {str(e)}")

    def on_table_select(self, table_name):
        """Handle table selection"""
        self.table_var.set(table_name)
        # Update button styles
        for btn in self.table_buttons:
            if btn.cget("text") == table_name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")
        self.log(f"Tabela selecionada: {table_name}")

    def log(self, message):
        """Add message to log"""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.dialog.update_idletasks()

    def start_import(self):
        """Start import process"""
        file_path = self.file_var.get().strip()
        if not file_path:
            messagebox.showerror("Erro", "Selecione ou digite o caminho do arquivo JSON")
            return

        file_path = os.path.expanduser(file_path)

        if not os.path.exists(file_path):
            messagebox.showerror(
                "Erro",
                f"Arquivo não encontrado:\n{file_path}\n\n"
                "Verifique se o caminho está correto."
            )
            return

        if not os.path.isfile(file_path):
            messagebox.showerror("Erro", f"O caminho especificado não é um arquivo: {file_path}")
            return

        if not file_path.lower().endswith('.json'):
            response = messagebox.askyesno(
                "Aviso",
                f"O arquivo não tem extensão .json:\n{file_path}\n\n"
                "Deseja continuar mesmo assim?"
            )
            if not response:
                return

        table_name = self.table_var.get().strip()
        if not table_name:
            messagebox.showerror("Erro", "Selecione ou digite o nome da tabela")
            return

        if not config.DYNAMODB_LOCAL:
            messagebox.showerror(
                "Erro de Segurança",
                "❌ Modo não é LOCAL! Importação cancelada por segurança."
            )
            return

        # Clear log and reset progress
        self.log_text.configure(state="normal")
        self.log_text.delete("0.0", "end")
        self.log_text.insert("0.0", "🚀 Preparando importação...\n")
        self.log_text.configure(state="disabled")

        # Start progress animation
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.progress_var.set("Importando... (processando itens)")

        # Disable import button
        self.import_btn.configure(state="disabled")

        # Start import in thread
        thread = threading.Thread(target=self._do_import, args=(file_path, table_name), daemon=True)
        thread.start()

    def _do_import(self, file_path, table_name):
        """Execute import in separate thread"""
        try:
            if not os.path.exists(file_path):
                error_msg = f"Arquivo não encontrado: {file_path}"
                self.dialog.after(0, lambda: self.log(f"❌ {error_msg}"))
                self.dialog.after(0, lambda: messagebox.showerror("Erro", error_msg))
                self.dialog.after(0, lambda: self.import_btn.configure(state="normal"))
                self.dialog.after(0, lambda: self.progress_bar.stop())
                return

            self.dialog.after(0, lambda: self.log("🚀 Iniciando importação..."))
            self.dialog.after(0, lambda: self.log(f"📁 Arquivo: {os.path.basename(file_path)}"))
            self.dialog.after(0, lambda: self.log(f"📊 Tabela: {table_name}"))
            self.dialog.after(0, lambda: self.log("⏳ Processando..."))
            self.dialog.after(0, lambda: self.log(""))

            import time
            start_time = time.time()
            last_update_time = start_time
            last_imported_count = 0

            def progress_callback(imported, total, error):
                nonlocal last_update_time, last_imported_count

                if error:
                    self.dialog.after(0, lambda msg=error: self.log(f"⚠️ {msg}"))

                current_time = time.time()
                elapsed = current_time - start_time

                if current_time - last_update_time >= 1.0 or imported > last_imported_count + 100:
                    if elapsed > 0:
                        velocity = imported / elapsed
                        status_text = f"Importados: {imported:,} itens | Velocidade: {velocity:.0f} itens/s"
                    else:
                        status_text = f"Importados: {imported:,} itens..."

                    self.dialog.after(0, lambda s=status_text: self.progress_var.set(s))
                    last_update_time = current_time
                    last_imported_count = imported

            success, imported_count, error_msg = self.db_service.import_data_from_file(
                file_path,
                table_name=table_name,
                progress_callback=progress_callback
            )

            # Stop progress animation
            self.dialog.after(0, lambda: self.progress_bar.stop())
            self.dialog.after(0, lambda: self.progress_bar.configure(mode="determinate"))
            self.dialog.after(0, lambda: self.progress_bar.set(1.0 if success else 0))

            if success:
                self.dialog.after(0, lambda: self.log(""))
                self.dialog.after(0, lambda: self.log("✅ Importação concluída com sucesso!"))
                self.dialog.after(0, lambda: self.log(f"📊 Total de itens importados: {imported_count}"))
                if error_msg:
                    self.dialog.after(0, lambda: self.log(f"ℹ️ {error_msg}"))

                self.dialog.after(0, lambda: self.progress_var.set(f"✅ Concluído: {imported_count} itens importados"))

                self.dialog.after(0, lambda: messagebox.showinfo(
                    "Importação Concluída",
                    f"✅ Importação concluída com sucesso!\n\n"
                    f"📊 Itens importados: {imported_count}\n"
                    f"📊 Tabela: {table_name}"
                ))
            else:
                self.dialog.after(0, lambda: self.log(""))
                self.dialog.after(0, lambda: self.log(f"❌ Erro na importação: {error_msg}"))
                self.dialog.after(0, lambda: self.progress_var.set(f"❌ Erro: {error_msg}"))

                self.dialog.after(0, lambda: messagebox.showerror(
                    "Erro na Importação",
                    f"❌ Erro ao importar dados:\n\n{error_msg}"
                ))

            # Re-enable import button
            self.dialog.after(0, lambda: self.import_btn.configure(state="normal"))

        except Exception as e:
            import traceback
            error_msg = f"Erro inesperado: {str(e)}"
            traceback_str = traceback.format_exc()
            self.dialog.after(0, lambda: self.log(f"❌ {error_msg}"))
            self.dialog.after(0, lambda: self.log(f"Detalhes: {traceback_str}"))
            self.dialog.after(0, lambda: self.progress_bar.stop())
            self.dialog.after(0, lambda: self.progress_var.set(f"❌ Erro: {error_msg}"))
            self.dialog.after(0, lambda: messagebox.showerror("Erro", f"{error_msg}\n\nVerifique o log para mais detalhes."))
            self.dialog.after(0, lambda: self.import_btn.configure(state="normal"))
