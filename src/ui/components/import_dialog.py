"""Import Dialog Component"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📥 Importar Dados - DynamoDB Local")
        self.dialog.geometry("700x800")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center window
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI components"""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=15, pady=15)
        
        title = ttk.Label(
            header_frame,
            text="📥 Importar Dados para DynamoDB Local",
            font=("Arial", 12, "bold")
        )
        title.pack()
        
        # Security warning
        warning_frame = ttk.LabelFrame(self.dialog, text="🔒 Segurança", padding=10)
        warning_frame.pack(fill=tk.X, padx=15, pady=5)
        
        warning_text = (
            "✓ Modo LOCAL ativo\n"
            "✓ Conexão com produção DESABILITADA\n"
            "✓ Dados serão importados apenas para o DynamoDB local"
        )
        ttk.Label(
            warning_frame,
            text=warning_text,
            foreground="green",
            font=("Arial", 9)
        ).pack(anchor=tk.W)
        
        # Table selection
        table_frame = ttk.LabelFrame(self.dialog, text="Tabela de Destino", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Table name input
        input_frame = ttk.Frame(table_frame)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(input_frame, text="Tabela:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.table_var = tk.StringVar(value=self.table_name or "")
        table_entry = ttk.Entry(input_frame, textvariable=self.table_var, width=40)
        table_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            input_frame,
            text="🔄 Atualizar",
            command=self.load_tables,
            width=12
        ).pack(side=tk.LEFT)
        
        # Table list
        list_frame = ttk.Frame(table_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        ttk.Label(
            list_frame,
            text="Lista de tabelas disponíveis:",
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=(0, 3))
        
        # Scrollbar for listbox
        list_scrollbar = ttk.Scrollbar(list_frame)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox for tables
        self.tables_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=list_scrollbar.set,
            height=6
        )
        self.tables_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.tables_listbox.yview)
        
        # Bind selection event
        self.tables_listbox.bind('<<ListboxSelect>>', self.on_table_select)
        
        # Load tables
        self.load_tables()
        
        # File selection
        file_frame = ttk.LabelFrame(self.dialog, text="Arquivo JSON", padding=10)
        file_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # File path input (editable)
        self.file_var = tk.StringVar(value="")
        file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=50)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Single button for file selection (combines both Selecionar and Dumps)
        ttk.Button(
            file_frame,
            text="📁 Selecionar Arquivo",
            command=self.select_file,
            width=25
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Hint
        ttk.Label(
            file_frame,
            text="💡 Dica: Digite o caminho do arquivo ou use os botões para navegar",
            font=("Arial", 8),
            foreground="gray"
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Progress
        progress_frame = ttk.LabelFrame(self.dialog, text="Progresso", padding=10)
        progress_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.progress_var = tk.StringVar(value="Aguardando início...")
        ttk.Label(
            progress_frame,
            textvariable=self.progress_var,
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=2)
        
        # Progress bar em modo indeterminado (para streaming de arquivo grande)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=550
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status log
        log_frame = ttk.LabelFrame(self.dialog, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Container for text and scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_container, height=8, wrap=tk.WORD, font=("Courier", 9))
        scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Inicializar log com mensagem
        self.log_text.insert(1.0, "📋 Pronto para importar. Selecione o arquivo e clique em 'Importar'.\n")
        self.log_text.config(state=tk.DISABLED)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=15, pady=15)
        
        ttk.Button(
            btn_frame,
            text="▶ Importar",
            command=self.start_import,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancelar",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
    
    def go_to_dumps_dir(self):
        """Open file dialog directly in dumps directory"""
        dumps_dir = "/home/joaquim/dumps/DynamoDB"
        if not os.path.exists(dumps_dir):
            dumps_dir = os.path.expanduser("~/dumps/DynamoDB")
        
        if os.path.exists(dumps_dir):
            filename = filedialog.askopenfilename(
                title="Selecionar arquivo JSON - Dumps",
                filetypes=[
                    ("Todos os arquivos", "*.*"),
                    ("JSON files", "*.json"),
                ],
                initialdir=dumps_dir
            )
        else:
            # Se o diretório não existir, criar ou mostrar erro
            filename = filedialog.askopenfilename(
                title="Selecionar arquivo JSON",
                filetypes=[
                    ("Todos os arquivos", "*.*"),
                    ("JSON files", "*.json"),
                ],
                initialdir=os.path.expanduser("~")
            )
            if not filename:
                messagebox.showinfo(
                    "Diretório não encontrado",
                    f"O diretório {dumps_dir} não foi encontrado.\n\n"
                    "Use o botão 'Selecionar' para navegar manualmente."
                )
        
        if filename:
            self.file_var.set(filename)
            self.log(f"Arquivo selecionado: {os.path.basename(filename)}")
    
    def select_file(self):
        """Open file dialog to select JSON file (prioritizes dumps directory)"""
        # Se já houver um caminho no campo, usar o diretório desse caminho
        current_path = self.file_var.get().strip()
        if current_path and os.path.exists(current_path):
            default_dir = os.path.dirname(current_path)
        elif current_path and os.path.dirname(current_path):
            default_dir = os.path.dirname(current_path)
        else:
            # Tentar usar o diretório de dumps como padrão
            default_dir = "/home/joaquim/dumps/DynamoDB"
            if not os.path.exists(default_dir):
                # Tentar outros diretórios comuns
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
            initialfile=""  # Não pré-selecionar nenhum arquivo
        )
        
        if filename:
            self.file_var.set(filename)
            self.log(f"Arquivo selecionado: {os.path.basename(filename)}")
    
    def load_tables(self):
        """Load list of tables from DynamoDB"""
        try:
            self.tables_listbox.delete(0, tk.END)
            tables = self.db_service.get_tables()
            
            if tables:
                for table in tables:
                    self.tables_listbox.insert(tk.END, table)
                
                # Se havia uma tabela pré-selecionada, selecionar ela na lista
                table_to_select = self.table_var.get().strip() or self.table_name
                if table_to_select and table_to_select in tables:
                    idx = tables.index(table_to_select)
                    self.tables_listbox.selection_set(idx)
                    self.tables_listbox.see(idx)
                    self.table_var.set(table_to_select)
            else:
                self.tables_listbox.insert(tk.END, "(Nenhuma tabela encontrada)")
                self.log("ℹ️ Nenhuma tabela encontrada. Certifique-se de que o DynamoDB Local está rodando.")
        
        except Exception as e:
            self.tables_listbox.insert(tk.END, f"(Erro ao carregar: {str(e)})")
            self.log(f"⚠️ Erro ao carregar tabelas: {str(e)}")
    
    def on_table_select(self, event):
        """Handle table selection from listbox"""
        selection = self.tables_listbox.curselection()
        if selection:
            table_name = self.tables_listbox.get(selection[0])
            # Não atualizar se for mensagem de erro
            if not table_name.startswith("("):
                self.table_var.set(table_name)
                self.log(f"Tabela selecionada: {table_name}")
    
    def log(self, message):
        """Add message to log"""
        # Habilitar edição, adicionar mensagem, desabilitar novamente
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.dialog.update_idletasks()
    
    def start_import(self):
        """Start import process"""
        # Validations
        file_path = self.file_var.get().strip()
        if not file_path:
            messagebox.showerror("Erro", "Selecione ou digite o caminho do arquivo JSON")
            return
        
        # Expandir ~ se presente
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
        
        # Verificar extensão
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
        
        # Verificar novamente se está em modo local (segurança extra)
        if not config.DYNAMODB_LOCAL:
            messagebox.showerror(
                "Erro de Segurança",
                "❌ Modo não é LOCAL! Importação cancelada por segurança."
            )
            return
        
        # Limpar log anterior e resetar progresso
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(1.0, "🚀 Preparando importação...\n")
        self.log_text.config(state=tk.DISABLED)
        
        # Iniciar barra indeterminada (para streaming sem total conhecido)
        self.progress_bar.start()
        self.progress_var.set("Importando... (processando itens)")
        self.dialog.update()
        
        # Disable any import/start buttons present (both bottom and quick-start)
        import_btns = []
        target_texts = {"📥 Importar", "▶ Iniciar", "Iniciar"}
        for widget in self.dialog.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, ttk.Frame):
                    for btn in child.winfo_children():
                        try:
                            if isinstance(btn, ttk.Button) and btn.cget("text") in target_texts:
                                import_btns.append(btn)
                                btn.config(state="disabled")
                        except Exception:
                            # Em alguns temas ou wrappers, cget pode falhar — ignore
                            pass

        # Start import in thread
        thread = threading.Thread(target=self._do_import, args=(file_path, table_name, import_btns), daemon=True)
        thread.start()
    
    def _do_import(self, file_path, table_name, import_btns=None):
        """Execute import in separate thread"""
        try:
            # Verificar arquivo novamente
            if not os.path.exists(file_path):
                error_msg = f"Arquivo não encontrado: {file_path}"
                self.log(f"❌ {error_msg}")
                self.dialog.after(0, lambda: messagebox.showerror("Erro", error_msg))
                if import_btns:
                    for b in import_btns:
                        try:
                            self.dialog.after(0, lambda btn=b: btn.config(state="normal"))
                        except Exception:
                            pass
                return
            
            # Log inicial
            self.dialog.after(0, lambda: self.log("🚀 Iniciando importação..."))
            self.dialog.after(0, lambda: self.log(f"📁 Arquivo: {os.path.basename(file_path)}"))
            self.dialog.after(0, lambda: self.log(f"📊 Tabela: {table_name}"))
            self.dialog.after(0, lambda: self.log("⏳ Processando... (barra animada = está funcionando)"))
            self.dialog.after(0, lambda: self.log(""))
            
            # Tracking do tempo e itens para calcular velocidade
            import time
            start_time = time.time()
            last_update_time = start_time
            last_imported_count = 0
            
            # Progress callback
            def progress_callback(imported, total, error):
                nonlocal last_update_time, last_imported_count
                
                if error:
                    self.dialog.after(0, lambda msg=error: self.log(f"⚠️ {msg}"))
                
                # Calcular velocidade (itens por segundo)
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Atualizar apenas a cada segundo para não poluir a UI
                if current_time - last_update_time >= 1.0 or imported > last_imported_count + 100:
                    if elapsed > 0:
                        velocity = imported / elapsed  # itens por segundo
                        eta_minutes = (0 / velocity) if velocity > 0 else 0  # Sem total, não há ETA
                        status_text = f"Importados: {imported:,} itens | Velocidade: {velocity:.0f} itens/s"
                    else:
                        status_text = f"Importados: {imported:,} itens..."
                    
                    self.dialog.after(0, lambda s=status_text: self.progress_var.set(s))
                    last_update_time = current_time
                    last_imported_count = imported
            
            # Import
            success, imported_count, error_msg = self.db_service.import_data_from_file(
                file_path,
                table_name=table_name,
                progress_callback=progress_callback
            )
            
            # Parar barra animada
            self.dialog.after(0, lambda: self.progress_bar.stop())
            
            # Final status
            if success:
                self.log("")
                self.log(f"✅ Importação concluída com sucesso!")
                self.log(f"📊 Total de itens importados: {imported_count}")
                if error_msg:
                    self.log(f"ℹ️ {error_msg}")
                
                self.progress_var.set(f"✅ Concluído: {imported_count} itens importados")
                
                # Show success message
                self.dialog.after(0, lambda: messagebox.showinfo(
                    "Importação Concluída",
                    f"✅ Importação concluída com sucesso!\n\n"
                    f"📊 Itens importados: {imported_count}\n"
                    f"📊 Tabela: {table_name}"
                ))
                # Re-enable import buttons
                if import_btns:
                    for b in import_btns:
                        try:
                            self.dialog.after(0, lambda btn=b: btn.config(state="normal"))
                        except Exception:
                            pass
            else:
                self.log("")
                self.log(f"❌ Erro na importação: {error_msg}")
                self.progress_var.set(f"❌ Erro: {error_msg}")
                self.progress_bar.stop()
                
                # Show error message
                self.dialog.after(0, lambda: messagebox.showerror(
                    "Erro na Importação",
                    f"❌ Erro ao importar dados:\n\n{error_msg}"
                ))
                # Re-enable import buttons
                if import_btns:
                    for b in import_btns:
                        try:
                            self.dialog.after(0, lambda btn=b: btn.config(state="normal"))
                        except Exception:
                            pass
        
        except Exception as e:
            import traceback
            error_msg = f"Erro inesperado: {str(e)}"
            traceback_str = traceback.format_exc()
            self.log(f"❌ {error_msg}")
            self.log(f"Detalhes: {traceback_str}")
            self.progress_bar.stop()
            self.progress_var.set(f"❌ Erro: {error_msg}")
            self.dialog.after(0, lambda: messagebox.showerror("Erro", f"{error_msg}\n\nVerifique o log para mais detalhes."))
            # Re-enable import buttons
            if import_btns:
                for b in import_btns:
                    try:
                        self.dialog.after(0, lambda btn=b: btn.config(state="normal"))
                    except Exception:
                        pass
