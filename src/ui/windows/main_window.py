"""Main Application Window"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
from decimal import Decimal

from src.models import FilterRow
from src.ui.components import LoadingIndicator, ImportDialog
from src.services import DynamoDBService
from src.utils.encoders import DecimalEncoder
from src.utils.resource_paths import load_icon_for_tk
from src.config import config


class MainWindow:
    """Main application window class"""
    
    def __init__(self, root):
        """Initialize main window
        
        Args:
            root: Root tkinter window
        """
        self.root = root
        self.root.title(config.APP_TITLE)
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        # Ícone da janela (logo da aplicação)
        load_icon_for_tk(self.root)
        
        # Services and state
        self.db_service = DynamoDBService()
        self.current_items = []
        self.filter_rows = []
        self.all_attributes = []
        self.selected_index = None
        
        # UI setup
        self.setup_ui()
        self.setup_connection()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main paned window (horizontal split)
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Table list
        left_frame = ttk.Frame(main_paned, width=200)
        main_paned.add(left_frame, weight=1)
        
        # Right panel
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=4)
        
        self._setup_left_panel(left_frame)
        self._setup_right_panel(right_frame)
    
    def _setup_left_panel(self, parent):
        """Setup left panel with table list"""
        # Header with server info
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            header_frame, 
            text="Tabelas DynamoDB", 
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT)
        
        # Button to change server
        ttk.Button(
            header_frame,
            text="⚙️ Mudar Servidor",
            command=self.change_server,
            width=20
        ).pack(side=tk.RIGHT, padx=5)
        
        # Refresh button
        ttk.Button(
            parent, 
            text="🔄 Atualizar", 
            command=self.load_tables
        ).pack(pady=5, fill=tk.X, padx=5)
        
        # Import button (only in local mode)
        if config.DYNAMODB_LOCAL:
            ttk.Button(
                parent,
                text="📥 Importar Dados",
                command=self.show_import_dialog,
                width=20
            ).pack(pady=5, fill=tk.X, padx=5)
        
        # Table list frame
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Table listbox
        self.tables_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set
        )
        self.tables_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tables_listbox.yview)
        
        self.tables_listbox.bind('<<ListboxSelect>>', self.on_table_select)
        
        # Connection status
        self.connection_label = ttk.Label(
            parent, 
            text="Desconectado", 
            foreground="red"
        )
        self.connection_label.pack(pady=5)
    
    def _setup_right_panel(self, parent):
        """Setup right panel with data and filters"""
        # Notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Data with filters
        self.data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_frame, text="📊 Dados com Filtros")
        self._setup_data_with_filters_tab(self.data_frame)
        
        # Tab 2: Table info
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="ℹ️ Info")
        self._setup_info_tab(self.info_frame)
    
    def _setup_data_with_filters_tab(self, parent):
        """Setup data display tab with filters"""
        # Index selector frame
        index_frame = ttk.LabelFrame(parent, text="🔍 Selecionar Índice (opcional)")
        index_frame.pack(fill=tk.X, padx=5, pady=5)
        
        index_controls = ttk.Frame(index_frame)
        index_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(index_controls, text="Índice:").pack(side=tk.LEFT, padx=5)
        
        self.index_var = tk.StringVar(value="")
        self.index_combo = ttk.Combobox(
            index_controls,
            textvariable=self.index_var,
            state="readonly",
            width=40
        )
        self.index_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.index_combo.bind('<<ComboboxSelected>>', self.on_index_selected)
        
        ttk.Label(index_controls, text="Tip: Usar índice acelera buscas", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=5)
        
        # Mensagem quando índices não carregam (ex: sem permissão DescribeTable)
        self.index_error_label = ttk.Label(
            index_frame,
            text="",
            font=("Arial", 8),
            foreground="darkorange",
            wraplength=500
        )
        self.index_error_label.pack(anchor=tk.W, padx=5, pady=(0, 5))
        
        # Filters frame
        filters_frame = ttk.LabelFrame(parent, text="▼ Filtros - opcional")
        filters_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Container for filter rows
        self.filters_container = ttk.Frame(filters_frame)
        self.filters_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Filter action buttons
        filter_actions = ttk.Frame(filters_frame)
        filter_actions.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            filter_actions, 
            text="➕ Adicionar filtro", 
            command=self.add_filter_row
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            filter_actions, 
            text="▶ Executar", 
            command=self.execute_filters
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            filter_actions, 
            text="🔄 Redefinir", 
            command=self.reset_filters
        ).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(filter_actions, text="")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Separator
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        # Data toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            toolbar, 
            text="📥 Carregar Tudo", 
            command=self.load_all_data
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(toolbar, text="Limite:").pack(side=tk.LEFT, padx=5)
        
        self.limit_var = tk.StringVar(value="50")
        ttk.Spinbox(
            toolbar, 
            from_=10, 
            to=1000, 
            textvariable=self.limit_var, 
            width=10
        ).pack(side=tk.LEFT)
        
        ttk.Label(toolbar, text="(↑ aumenta / ↓ diminui para mais/menos velocidade)", font=("Arial", 8, "italic")).pack(side=tk.LEFT, padx=5)
        
        self.count_label = ttk.Label(toolbar, text="Items: 0")
        self.count_label.pack(side=tk.RIGHT, padx=5)
        
        # Item actions frame
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            actions_frame,
            text="🗑️ Deletar Item Selecionado",
            command=self.delete_selected_item
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            actions_frame,
            text="🗑️ Deletar Vários Itens",
            command=self.delete_multiple_items
        ).pack(side=tk.LEFT, padx=2)
        
        # Help text
        ttk.Label(
            actions_frame,
            text="💡 Dica: Use Ctrl+Click ou Shift+Click para selecionar múltiplos itens",
            font=("Arial", 8, "italic"),
            foreground="gray"
        ).pack(side=tk.LEFT, padx=15)
        
        self.action_status_label = ttk.Label(actions_frame, text="", foreground="green")
        self.action_status_label.pack(side=tk.LEFT, padx=10)
        
        # Treeview frame
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        self.data_tree = ttk.Treeview(
            tree_frame, 
            yscrollcommand=vsb.set, 
            xscrollcommand=hsb.set,
            selectmode='extended'  # Enable multiple selection with Ctrl+Click or Shift+Click
        )
        vsb.config(command=self.data_tree.yview)
        hsb.config(command=self.data_tree.xview)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.data_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind for double-click
        self.data_tree.bind('<Double-1>', self.show_item_details)
    
    def _setup_info_tab(self, parent):
        """Setup table info tab"""
        self.info_text = scrolledtext.ScrolledText(parent, height=20)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_connection(self):
        """Setup DynamoDB connection"""
        if self.db_service.connect():
            connection_text = "✓ Conectado ao DynamoDB Local" if config.DYNAMODB_LOCAL else "✓ Conectado ao AWS"
            self.connection_label.config(
                text=connection_text, 
                foreground="green"
            )
            self.load_tables()
        else:
            error_msg = (
                "Configure DynamoDB Local em: http://localhost:8000\n"
                "Ou configure o AWS CLI com: aws configure"
            ) if config.DYNAMODB_LOCAL else (
                "Configure o AWS CLI com: aws configure"
            )
            
            self.connection_label.config(
                text="✗ Erro de conexão", 
                foreground="red"
            )
            messagebox.showerror(
                "Erro de Conexão",
                f"Erro ao conectar ao DynamoDB.\n\n{error_msg}"
            )
    
    def change_server(self):
        """Change server/environment - Close current window and reopen selector"""
        from src.ui.components.environment_selector import EnvironmentSelector
        
        confirm = messagebox.askyesno(
            "Mudar Servidor",
            "Deseja realmente mudar de servidor?\n\nA janela será fechada e o seletor de servidor será aberto novamente."
        )
        
        if not confirm:
            return
        
        self.root.destroy()
        
        selector_root = tk.Tk()
        selector = EnvironmentSelector(selector_root)
        selector_root.mainloop()
        
        if selector.result is None:
            return
        
        mode, value = selector.result
        
        if mode == "local":
            config.set_local(value)
        else:
            config.set_production(value)
        
        config.print_config()
        
        app_root = tk.Tk()
        app = MainWindow(app_root)
        app_root.mainloop()
    
    def load_tables(self):
        """Load list of tables"""
        try:
            self.tables_listbox.delete(0, tk.END)
            tables = self.db_service.get_tables()
            
            for table in tables:
                self.tables_listbox.insert(tk.END, table)
            
            if not tables:
                messagebox.showinfo(
                    "Info", 
                    "Nenhuma tabela encontrada no DynamoDB"
                )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar tabelas:\n{str(e)}")
    
    def on_table_select(self, event):
        """Callback when a table is selected"""
        selection = self.tables_listbox.curselection()
        if selection:
            table_name = self.tables_listbox.get(selection[0])
            
            # Start loading indicator
            loading = LoadingIndicator(self.status_label)
            loading.start(f"Carregando tabela: {table_name}")
            
            # Disable table selection while loading
            self.tables_listbox.config(state=tk.DISABLED)
            
            def load_in_thread():
                try:
                    self.db_service.select_table(table_name)
                    self.show_table_info()
                    self.load_table_attributes()
                    self.load_table_indexes()
                    self.reset_filters()
                    
                    # Success message
                    self.root.after(0, lambda: loading.stop_success(f"Tabela carregada: {table_name}"))
                except Exception as e:
                    self.root.after(0, lambda: loading.stop_error(f"Erro ao carregar tabela: {str(e)}"))
                finally:
                    # Re-enable table selection
                    self.root.after(0, lambda: self.tables_listbox.config(state=tk.NORMAL))
            
            # Run in separate thread to not block UI
            thread = threading.Thread(target=load_in_thread, daemon=True)
            thread.start()
    
    def load_table_attributes(self):
        """Load table attributes for filters"""
        self.all_attributes = self.db_service.get_table_attributes()
    
    def load_table_indexes(self):
        """Load available indexes for current table"""
        indexes = self.db_service.get_table_indexes()
        err = getattr(self.db_service, "last_index_error", None)
        
        # Mostrar mensagem quando índices não carregam por falta de permissão
        if err and ("AccessDenied" in err or "DescribeTable" in err):
            self.index_error_label.config(
                text="⚠ Sem permissão dynamodb:DescribeTable. Adicione essa ação na política IAM da tabela para listar índices e usar consultas rápidas (Query)."
            )
        else:
            self.index_error_label.config(text="")
        
        index_list = []
        if indexes["gsi"]:
            for idx in indexes["gsi"]:
                index_list.append(f"[GSI] {idx}")
        if indexes["lsi"]:
            for idx in indexes["lsi"]:
                index_list.append(f"[LSI] {idx}")
        
        self.index_combo['values'] = ["(Nenhum)"] + index_list
        self.index_combo.set("(Nenhum)")
    
    def on_index_selected(self, event=None):
        """Callback when an index is selected"""
        selected = self.index_var.get()
        if selected and selected != "(Nenhum)":
            self.selected_index = selected.split("] ")[1] if "] " in selected else selected
            print(f"[INDEX] Usando índice: {self.selected_index}")
        else:
            self.selected_index = None
            print("[INDEX] Nenhum índice selecionado")
    
    def add_filter_row(self):
        """Add a new filter row"""
        filter_row = FilterRow(
            self.filters_container, 
            self.remove_filter_row, 
            self.all_attributes
        )
        filter_row.pack()
        self.filter_rows.append(filter_row)
    
    def remove_filter_row(self, row):
        """Remove a filter row"""
        if row in self.filter_rows:
            self.filter_rows.remove(row)
    
    def reset_filters(self):
        """Reset all filters"""
        for row in self.filter_rows[:]:
            row.remove()
        self.filter_rows = []
        self.status_label.config(text="")
    
    def execute_filters(self):
        """Execute query with applied filters"""
        if not self.db_service.current_table:
            messagebox.showwarning("Aviso", "Selecione uma tabela primeiro")
            return
        
        self.loading_indicator = LoadingIndicator(self.status_label)
        
        thread = threading.Thread(target=self._do_execute_filters, daemon=True)
        thread.start()
    
    def _do_execute_filters(self):
        """Execute filters in separate thread"""
        try:
            self.loading_indicator.start("Carregando dados...")
            
            limit = int(self.limit_var.get())
            
            filters = [
                row.get_filter() for row in self.filter_rows 
                if row.get_filter()
            ]
            
            print(f"[EXECUTE_FILTERS] Índice selecionado: {self.selected_index}")
            print(f"[EXECUTE_FILTERS] Limite: {limit} itens")
            items, scanned_count, elapsed = self.db_service.query_with_filters(
                filters, 
                limit,
                index_name=self.selected_index,
                known_attributes=self.all_attributes
            )
            
            self.current_items = items
            
            message = f"Items: {len(items)} | Verificados: {scanned_count} | Tempo: {elapsed:.2f}s"
            self.root.after(0, lambda: self.display_items(items))
            self.root.after(0, lambda: self.loading_indicator.stop_success(message))
        
        except Exception as e:
            error_msg = f"Erro ao executar filtros: {str(e)}"
            self.root.after(
                0, 
                lambda: self.loading_indicator.stop_error(error_msg)
            )
            self.root.after(
                0, 
                lambda: messagebox.showerror("Erro", error_msg)
            )
    
    def load_all_data(self):
        """Load all data without filters"""
        self.reset_filters()
        self.execute_filters()
    
    def display_items(self, items):
        """Display items in treeview"""
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        if not items:
            self.data_tree["columns"] = []
            return
        
        all_keys = set()
        for item in items:
            all_keys.update(item.keys())
        
        columns = sorted(list(all_keys))
        
        self.data_tree["columns"] = columns
        self.data_tree["show"] = "headings"
        
        # Calculate column widths based on content
        col_widths = {}
        for col in columns:
            # Start with column name length
            max_width = len(str(col)) + 5
            
            # Check all values in this column
            for item in items:
                value = item.get(col, "")
                if isinstance(value, Decimal):
                    value = float(value)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)[:100]
                
                value_str = str(value)
                width = len(value_str) + 2
                max_width = max(max_width, min(width, 250))  # Cap at 250px
            
            col_widths[col] = max_width
        
        # Set headings and column widths
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=col_widths[col], minwidth=50)
        
        # Insert data rows
        for item in items:
            values = []
            for col in columns:
                value = item.get(col, "")
                if isinstance(value, Decimal):
                    value = float(value)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)[:100] + "..."
                values.append(str(value))
            
            self.data_tree.insert("", tk.END, values=values)
    
    def delete_selected_item(self):
        """Delete the selected item from the table"""
        selection = self.data_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um item para deletar")
            return
        
        item_index = self.data_tree.index(selection[0])
        if item_index >= len(self.current_items):
            messagebox.showerror("Erro", "Índice do item inválido")
            return
        
        item = self.current_items[item_index]
        
        # Get primary key from the table schema
        try:
            self.db_service.current_table.reload()
            key_schema = self.db_service.current_table.key_schema
            
            # Extract key from item
            key = {}
            for key_attr in key_schema:
                attr_name = key_attr['AttributeName']
                if attr_name not in item:
                    messagebox.showerror(
                        "Erro",
                        f"Atributo chave '{attr_name}' não encontrado no item"
                    )
                    return
                key[attr_name] = item[attr_name]
            
            # Show confirmation dialog with item details
            item_preview = json.dumps(item, indent=2, ensure_ascii=False, cls=DecimalEncoder)[:200]
            confirm = messagebox.askyesno(
                "Confirmar Deleção",
                f"Tem certeza que deseja deletar este item?\n\n"
                f"Chave: {key}\n\n"
                f"Preview do item:\n{item_preview}..."
            )
            
            if not confirm:
                return
            
            # Delete the item
            success, message = self.db_service.delete_item(key)
            
            if success:
                # Remove from UI
                self.data_tree.delete(selection[0])
                self.current_items.pop(item_index)
                
                # Update count
                self.count_label.config(text=f"Items: {len(self.current_items)}")
                
                # Show success message
                self.action_status_label.config(
                    text=f"✓ {message}",
                    foreground="green"
                )
                
                messagebox.showinfo("Sucesso", message)
            else:
                self.action_status_label.config(
                    text=f"✗ Erro ao deletar",
                    foreground="red"
                )
                messagebox.showerror("Erro", message)
        
        except Exception as e:
            error_msg = f"Erro ao deletar item: {str(e)}"
            messagebox.showerror("Erro", error_msg)
    
    def delete_multiple_items(self):
        """Delete multiple selected items from the table"""
        selection = self.data_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione pelo menos um item para deletar")
            return
        
        if len(selection) == 1:
            messagebox.showinfo("Aviso", "Use 'Deletar Item Selecionado' para deletar apenas um item.\n\nPara deletar vários, use Ctrl+Click para selecionar múltiplos itens.")
            return
        
        # Get primary key schema
        try:
            self.db_service.current_table.reload()
            key_schema = self.db_service.current_table.key_schema
            
            # Collect items to delete
            items_to_delete = []
            for selection_item in selection:
                item_index = self.data_tree.index(selection_item)
                if item_index >= len(self.current_items):
                    continue
                
                item = self.current_items[item_index]
                
                # Extract key from item
                key = {}
                for key_attr in key_schema:
                    attr_name = key_attr['AttributeName']
                    if attr_name in item:
                        key[attr_name] = item[attr_name]
                
                items_to_delete.append({
                    'item': item,
                    'key': key,
                    'tree_item': selection_item,
                    'index': item_index
                })
            
            if not items_to_delete:
                messagebox.showerror("Erro", "Não foi possível identificar os itens selecionados")
                return
            
            # Show confirmation dialog
            confirm_msg = f"Tem certeza que deseja deletar {len(items_to_delete)} itens?\n\n"
            confirm_msg += "Itens a serem deletados:\n"
            for i, item_data in enumerate(items_to_delete[:5], 1):
                confirm_msg += f"{i}. {json.dumps(item_data['key'], ensure_ascii=False, cls=DecimalEncoder)}\n"
            
            if len(items_to_delete) > 5:
                confirm_msg += f"... e mais {len(items_to_delete) - 5} itens\n"
            
            confirm_msg += "\nEsta ação é irreversível!"
            
            confirm = messagebox.askyesno(
                "Confirmar Deleção em Lote",
                confirm_msg
            )
            
            if not confirm:
                return
            
            # Delete items with progress feedback
            deleted_count = 0
            errors = []
            
            self.action_status_label.config(
                text=f"Deletando {len(items_to_delete)} itens...",
                foreground="blue"
            )
            self.root.update()
            
            for item_data in items_to_delete:
                success, message = self.db_service.delete_item(item_data['key'])
                
                if success:
                    deleted_count += 1
                    # Remove from UI
                    self.data_tree.delete(item_data['tree_item'])
                else:
                    errors.append(f"Erro ao deletar {item_data['key']}: {message}")
            
            # Remove deleted items from current_items list (in reverse order to maintain indices)
            for item_data in sorted(items_to_delete, key=lambda x: x['index'], reverse=True):
                self.current_items.pop(item_data['index'])
            
            # Update count
            self.count_label.config(text=f"Items: {len(self.current_items)}")
            
            # Show result
            if deleted_count == len(items_to_delete):
                result_msg = f"✓ {deleted_count} itens deletados com sucesso!"
                self.action_status_label.config(
                    text=result_msg,
                    foreground="green"
                )
                messagebox.showinfo("Sucesso", result_msg)
            else:
                result_msg = f"Deletados: {deleted_count}/{len(items_to_delete)} itens"
                if errors:
                    result_msg += f"\n\nErros:\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        result_msg += f"\n... e mais {len(errors) - 5} erros"
                
                self.action_status_label.config(
                    text=f"⚠️ {deleted_count}/{len(items_to_delete)} deletados",
                    foreground="orange"
                )
                messagebox.showwarning("Resultado da Deleção", result_msg)
        
        except Exception as e:
            error_msg = f"Erro ao deletar múltiplos itens: {str(e)}"
            self.action_status_label.config(
                text="✗ Erro ao deletar",
                foreground="red"
            )
            messagebox.showerror("Erro", error_msg)
    
    def show_item_details(self, event):
        """Show item details in a popup window"""
        selection = self.data_tree.selection()
        if not selection:
            return
        
        item_index = self.data_tree.index(selection[0])
        if item_index >= len(self.current_items):
            return
        
        item = self.current_items[item_index]
        
        popup = tk.Toplevel(self.root)
        popup.title("Detalhes do Item")
        popup.geometry("600x400")
        
        text = scrolledtext.ScrolledText(popup)
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        json_str = json.dumps(
            item, 
            indent=2, 
            ensure_ascii=False, 
            cls=DecimalEncoder
        )
        text.insert(1.0, json_str)
        text.config(state=tk.DISABLED)
    
    def show_table_info(self):
        """Display table information"""
        try:
            info = self.db_service.get_table_info()
            
            info_text = json.dumps(
                info, 
                indent=2, 
                ensure_ascii=False, 
                default=str
            )
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
        
        except Exception as e:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, f"Erro ao carregar info:\n{str(e)}")
    
    def show_import_dialog(self):
        """Show import dialog for importing data to local DynamoDB"""
        # Verificar se está em modo local (segurança)
        if not config.DYNAMODB_LOCAL:
            messagebox.showerror(
                "Erro de Segurança",
                "❌ Importação só é permitida em modo LOCAL!\n\n"
                "Por segurança, esta funcionalidade não funciona quando conectado à produção."
            )
            return
        
        # Obter nome da tabela selecionada se houver
        table_name = None
        selection = self.tables_listbox.curselection()
        if selection:
            table_name = self.tables_listbox.get(selection[0])
        
        # Abrir diálogo de importação
        dialog = ImportDialog(self.root, self.db_service, table_name=table_name)
        
        # Após fechar o diálogo, atualizar tabelas se necessário
        if dialog and hasattr(dialog, 'result'):
            self.load_tables()
