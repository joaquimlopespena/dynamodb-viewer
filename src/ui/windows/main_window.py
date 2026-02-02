"""Main Application Window"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from decimal import Decimal

from src.models import FilterRow
from src.ui.components import LoadingIndicator, ImportDialog
from src.services import DynamoDBService
from src.utils.encoders import DecimalEncoder
from src.utils.resource_paths import load_icon_for_ctk
from src.config import config


class MainWindow:
    """Main application window class"""

    def __init__(self, root):
        """Initialize main window

        Args:
            root: Root CTk window
        """
        self.root = root
        self.root.title(config.APP_TITLE)
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")

        # Ícone da janela
        load_icon_for_ctk(self.root)

        # Services and state
        self.db_service = DynamoDBService()
        self.current_items = []
        self.filter_rows = []
        self.all_attributes = []
        self.selected_index = None

        # Configure dark theme for ttk widgets (Treeview)
        self._configure_treeview_style()

        # UI setup
        self.setup_ui()
        self.setup_connection()

    def _configure_treeview_style(self):
        """Configure ttk style for dark theme compatibility"""
        style = ttk.Style()

        # Dark theme colors
        bg_color = "#2b2b2b"
        fg_color = "#ffffff"
        selected_color = "#1f538d"

        style.theme_use("clam")

        style.configure(
            "Dark.Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            borderwidth=0,
            rowheight=28
        )
        style.configure(
            "Dark.Treeview.Heading",
            background="#3d3d3d",
            foreground=fg_color,
            borderwidth=0,
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "Dark.Treeview",
            background=[("selected", selected_color)],
            foreground=[("selected", fg_color)]
        )
        style.map(
            "Dark.Treeview.Heading",
            background=[("active", "#4d4d4d")]
        )

        # Scrollbar style
        style.configure(
            "Dark.Vertical.TScrollbar",
            background="#3d3d3d",
            troughcolor=bg_color,
            borderwidth=0
        )
        style.configure(
            "Dark.Horizontal.TScrollbar",
            background="#3d3d3d",
            troughcolor=bg_color,
            borderwidth=0
        )

    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Configure grid
        main_container.grid_columnconfigure(0, weight=1, minsize=220)
        main_container.grid_columnconfigure(1, weight=4)
        main_container.grid_rowconfigure(0, weight=1)

        # Left panel - Table list
        left_frame = ctk.CTkFrame(main_container)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Right panel
        right_frame = ctk.CTkFrame(main_container)
        right_frame.grid(row=0, column=1, sticky="nsew")

        self._setup_left_panel(left_frame)
        self._setup_right_panel(right_frame)

    def _setup_left_panel(self, parent):
        """Setup left panel with table list"""
        # Header
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header_frame,
            text="Tabelas DynamoDB",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        # Button to change server
        ctk.CTkButton(
            header_frame,
            text="⚙️ Mudar",
            command=self.change_server,
            width=80,
            height=28,
            font=ctk.CTkFont(size=11)
        ).pack(side="right")

        # Refresh button
        ctk.CTkButton(
            parent,
            text="🔄 Atualizar Tabelas",
            command=self.load_tables,
            height=32
        ).pack(pady=5, fill="x", padx=10)

        # Import button (only in local mode)
        if config.DYNAMODB_LOCAL:
            ctk.CTkButton(
                parent,
                text="📥 Importar Dados",
                command=self.show_import_dialog,
                height=32,
                fg_color="#2d5a27",
                hover_color="#3d7a37"
            ).pack(pady=5, fill="x", padx=10)

        # Table list frame with scrollable frame
        list_container = ctk.CTkFrame(parent)
        list_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.tables_scrollable = ctk.CTkScrollableFrame(list_container)
        self.tables_scrollable.pack(fill="both", expand=True)

        # Store table buttons
        self.table_buttons = []
        self.selected_table_btn = None

        # Connection status
        self.connection_label = ctk.CTkLabel(
            parent,
            text="Desconectado",
            font=ctk.CTkFont(size=11),
            text_color="#ef5350"
        )
        self.connection_label.pack(pady=10)

    def _setup_right_panel(self, parent):
        """Setup right panel with data and filters"""
        # Tabview for tabs
        self.tabview = ctk.CTkTabview(parent)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Data with filters
        self.data_tab = self.tabview.add("📊 Dados com Filtros")
        self._setup_data_with_filters_tab(self.data_tab)

        # Tab 2: Table info
        self.info_tab = self.tabview.add("ℹ️ Info")
        self._setup_info_tab(self.info_tab)

    def _setup_data_with_filters_tab(self, parent):
        """Setup data display tab with filters"""
        # Index selector frame
        index_frame = ctk.CTkFrame(parent)
        index_frame.pack(fill="x", padx=5, pady=5)

        index_header = ctk.CTkLabel(
            index_frame,
            text="🔍 Selecionar Índice (opcional)",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        index_header.pack(anchor="w", padx=10, pady=(10, 5))

        index_controls = ctk.CTkFrame(index_frame, fg_color="transparent")
        index_controls.pack(fill="x", padx=10, pady=(0, 5))

        ctk.CTkLabel(index_controls, text="Índice:").pack(side="left", padx=5)

        self.index_var = ctk.StringVar(value="")
        self.index_combo = ctk.CTkComboBox(
            index_controls,
            variable=self.index_var,
            state="readonly",
            width=300,
            command=self.on_index_selected
        )
        self.index_combo.pack(side="left", padx=5)

        ctk.CTkLabel(
            index_controls,
            text="Tip: Usar índice acelera buscas",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(side="left", padx=10)

        # Index error label
        self.index_error_label = ctk.CTkLabel(
            index_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="#FFA726",
            wraplength=500
        )
        self.index_error_label.pack(anchor="w", padx=10, pady=(0, 10))

        # Filters frame
        filters_frame = ctk.CTkFrame(parent)
        filters_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            filters_frame,
            text="▼ Filtros - opcional",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(5, 2))

        # Container for filter rows (compact)
        self.filters_container = ctk.CTkFrame(filters_frame, fg_color="transparent")
        self.filters_container.pack(fill="x", padx=10, pady=2)

        # Filter action buttons
        filter_actions = ctk.CTkFrame(filters_frame, fg_color="transparent")
        filter_actions.pack(fill="x", padx=10, pady=(2, 8))

        ctk.CTkButton(
            filter_actions,
            text="➕ Adicionar filtro",
            command=self.add_filter_row,
            width=130,
            height=30
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_actions,
            text="▶ Executar",
            command=self.execute_filters,
            width=100,
            height=30,
            fg_color="#2d5a27",
            hover_color="#3d7a37"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_actions,
            text="🔄 Redefinir",
            command=self.reset_filters,
            width=100,
            height=30,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90")
        ).pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(
            filter_actions,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", padx=15)

        # Data toolbar
        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            toolbar,
            text="📥 Carregar Tudo",
            command=self.load_all_data,
            width=120,
            height=30
        ).pack(side="left", padx=2)

        ctk.CTkLabel(toolbar, text="Limite:").pack(side="left", padx=(15, 5))

        self.limit_var = ctk.StringVar(value="50")
        limit_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.limit_var,
            width=70,
            height=30
        )
        limit_entry.pack(side="left")

        ctk.CTkLabel(
            toolbar,
            text="(↑ aumenta / ↓ diminui)",
            font=ctk.CTkFont(size=10, slant="italic"),
            text_color="gray"
        ).pack(side="left", padx=10)

        self.count_label = ctk.CTkLabel(
            toolbar,
            text="Items: 0",
            font=ctk.CTkFont(size=11)
        )
        self.count_label.pack(side="right", padx=5)

        # Item actions frame
        actions_frame = ctk.CTkFrame(parent, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            actions_frame,
            text="🗑️ Deletar Selecionado",
            command=self.delete_selected_item,
            width=150,
            height=30,
            fg_color="#8b0000",
            hover_color="#a52a2a"
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions_frame,
            text="🗑️ Deletar Vários",
            command=self.delete_multiple_items,
            width=130,
            height=30,
            fg_color="#8b0000",
            hover_color="#a52a2a"
        ).pack(side="left", padx=2)

        ctk.CTkLabel(
            actions_frame,
            text="💡 Ctrl+Click ou Shift+Click para selecionar múltiplos",
            font=ctk.CTkFont(size=10, slant="italic"),
            text_color="gray"
        ).pack(side="left", padx=15)

        self.action_status_label = ctk.CTkLabel(
            actions_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#4CAF50"
        )
        self.action_status_label.pack(side="left", padx=10)

        # Treeview frame (using ttk.Treeview as CustomTkinter doesn't have one)
        tree_frame = ctk.CTkFrame(parent)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Inner frame for treeview
        tree_inner = tk.Frame(tree_frame, bg="#2b2b2b")
        tree_inner.pack(fill="both", expand=True, padx=2, pady=2)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_inner, orient="vertical", style="Dark.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(tree_inner, orient="horizontal", style="Dark.Horizontal.TScrollbar")

        # Treeview with dark style
        self.data_tree = ttk.Treeview(
            tree_inner,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode='extended',
            style="Dark.Treeview"
        )
        vsb.config(command=self.data_tree.yview)
        hsb.config(command=self.data_tree.xview)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.data_tree.pack(fill="both", expand=True)

        # Bind for double-click
        self.data_tree.bind('<Double-1>', self.show_item_details)

    def _setup_info_tab(self, parent):
        """Setup table info tab"""
        self.info_text = ctk.CTkTextbox(parent, font=ctk.CTkFont(family="Courier", size=12))
        self.info_text.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_connection(self):
        """Setup DynamoDB connection"""
        if self.db_service.connect():
            connection_text = "✓ Conectado ao DynamoDB Local" if config.DYNAMODB_LOCAL else "✓ Conectado ao AWS"
            self.connection_label.configure(
                text=connection_text,
                text_color="#4CAF50"
            )
            self.load_tables()
        else:
            error_msg = (
                "Configure DynamoDB Local em: http://localhost:8000\n"
                "Ou configure o AWS CLI com: aws configure"
            ) if config.DYNAMODB_LOCAL else (
                "Configure o AWS CLI com: aws configure"
            )

            self.connection_label.configure(
                text="✗ Erro de conexão",
                text_color="#ef5350"
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

        selector_root = ctk.CTk()
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

        app_root = ctk.CTk()
        app = MainWindow(app_root)
        app_root.mainloop()

    def load_tables(self):
        """Load list of tables"""
        try:
            # Clear existing buttons
            for btn in self.table_buttons:
                btn.destroy()
            self.table_buttons = []
            self.selected_table_btn = None

            tables = self.db_service.get_tables()

            for table in tables:
                btn = ctk.CTkButton(
                    self.tables_scrollable,
                    text=table,
                    command=lambda t=table: self.on_table_click(t),
                    height=32,
                    anchor="w",
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30")
                )
                btn.pack(fill="x", pady=1)
                self.table_buttons.append(btn)

            if not tables:
                messagebox.showinfo(
                    "Info",
                    "Nenhuma tabela encontrada no DynamoDB"
                )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar tabelas:\n{str(e)}")

    def on_table_click(self, table_name):
        """Handle table button click"""
        # Update button styles
        for btn in self.table_buttons:
            if btn.cget("text") == table_name:
                btn.configure(fg_color=("gray75", "gray25"))
                self.selected_table_btn = btn
            else:
                btn.configure(fg_color="transparent")

        # Start loading
        loading = LoadingIndicator(self.status_label)
        loading.start(f"Carregando: {table_name}")

        def load_in_thread():
            try:
                self.db_service.select_table(table_name)
                self.show_table_info()
                self.load_table_attributes()
                self.load_table_indexes()
                self.reset_filters()

                self.root.after(0, lambda: loading.stop_success(f"Tabela carregada: {table_name}"))
            except Exception as e:
                self.root.after(0, lambda: loading.stop_error(f"Erro: {str(e)}"))

        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()

    def on_table_select(self, event):
        """Callback when a table is selected (legacy compatibility)"""
        pass

    def load_table_attributes(self):
        """Load table attributes for filters"""
        self.all_attributes = self.db_service.get_table_attributes()

    def load_table_indexes(self):
        """Load available indexes for current table"""
        indexes = self.db_service.get_table_indexes()
        err = getattr(self.db_service, "last_index_error", None)

        if err and ("AccessDenied" in err or "DescribeTable" in err):
            self.index_error_label.configure(
                text="⚠ Sem permissão dynamodb:DescribeTable. Adicione essa ação na política IAM."
            )
        else:
            self.index_error_label.configure(text="")

        index_list = ["(Nenhum)"]
        if indexes["gsi"]:
            for idx in indexes["gsi"]:
                index_list.append(f"[GSI] {idx}")
        if indexes["lsi"]:
            for idx in indexes["lsi"]:
                index_list.append(f"[LSI] {idx}")

        self.index_combo.configure(values=index_list)
        self.index_combo.set("(Nenhum)")

    def on_index_selected(self, value=None):
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
        self.status_label.configure(text="")

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
            max_width = len(str(col)) + 5

            for item in items:
                value = item.get(col, "")
                if isinstance(value, Decimal):
                    value = float(value)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)[:100]

                value_str = str(value)
                width = len(value_str) + 2
                max_width = max(max_width, min(width, 250))

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

            self.data_tree.insert("", "end", values=values)

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

        try:
            self.db_service.current_table.reload()
            key_schema = self.db_service.current_table.key_schema

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

            item_preview = json.dumps(item, indent=2, ensure_ascii=False, cls=DecimalEncoder)[:200]
            confirm = messagebox.askyesno(
                "Confirmar Deleção",
                f"Tem certeza que deseja deletar este item?\n\n"
                f"Chave: {key}\n\n"
                f"Preview do item:\n{item_preview}..."
            )

            if not confirm:
                return

            success, message = self.db_service.delete_item(key)

            if success:
                self.data_tree.delete(selection[0])
                self.current_items.pop(item_index)
                self.count_label.configure(text=f"Items: {len(self.current_items)}")
                self.action_status_label.configure(
                    text=f"✓ {message}",
                    text_color="#4CAF50"
                )
                messagebox.showinfo("Sucesso", message)
            else:
                self.action_status_label.configure(
                    text="✗ Erro ao deletar",
                    text_color="#ef5350"
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
            messagebox.showinfo("Aviso", "Use 'Deletar Selecionado' para deletar apenas um item.\n\nPara deletar vários, use Ctrl+Click.")
            return

        try:
            self.db_service.current_table.reload()
            key_schema = self.db_service.current_table.key_schema

            items_to_delete = []
            for selection_item in selection:
                item_index = self.data_tree.index(selection_item)
                if item_index >= len(self.current_items):
                    continue

                item = self.current_items[item_index]

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

            confirm_msg = f"Tem certeza que deseja deletar {len(items_to_delete)} itens?\n\n"
            confirm_msg += "Itens a serem deletados:\n"
            for i, item_data in enumerate(items_to_delete[:5], 1):
                confirm_msg += f"{i}. {json.dumps(item_data['key'], ensure_ascii=False, cls=DecimalEncoder)}\n"

            if len(items_to_delete) > 5:
                confirm_msg += f"... e mais {len(items_to_delete) - 5} itens\n"

            confirm_msg += "\nEsta ação é irreversível!"

            confirm = messagebox.askyesno("Confirmar Deleção em Lote", confirm_msg)

            if not confirm:
                return

            deleted_count = 0
            errors = []

            self.action_status_label.configure(
                text=f"Deletando {len(items_to_delete)} itens...",
                text_color="#2196F3"
            )
            self.root.update()

            for item_data in items_to_delete:
                success, message = self.db_service.delete_item(item_data['key'])

                if success:
                    deleted_count += 1
                    self.data_tree.delete(item_data['tree_item'])
                else:
                    errors.append(f"Erro ao deletar {item_data['key']}: {message}")

            for item_data in sorted(items_to_delete, key=lambda x: x['index'], reverse=True):
                self.current_items.pop(item_data['index'])

            self.count_label.configure(text=f"Items: {len(self.current_items)}")

            if deleted_count == len(items_to_delete):
                result_msg = f"✓ {deleted_count} itens deletados com sucesso!"
                self.action_status_label.configure(
                    text=result_msg,
                    text_color="#4CAF50"
                )
                messagebox.showinfo("Sucesso", result_msg)
            else:
                result_msg = f"Deletados: {deleted_count}/{len(items_to_delete)} itens"
                if errors:
                    result_msg += f"\n\nErros:\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        result_msg += f"\n... e mais {len(errors) - 5} erros"

                self.action_status_label.configure(
                    text=f"⚠️ {deleted_count}/{len(items_to_delete)} deletados",
                    text_color="#FFA726"
                )
                messagebox.showwarning("Resultado da Deleção", result_msg)

        except Exception as e:
            error_msg = f"Erro ao deletar múltiplos itens: {str(e)}"
            self.action_status_label.configure(
                text="✗ Erro ao deletar",
                text_color="#ef5350"
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

        popup = ctk.CTkToplevel(self.root)
        popup.title("Detalhes do Item")
        popup.geometry("600x400")

        text = ctk.CTkTextbox(popup, font=ctk.CTkFont(family="Courier", size=12))
        text.pack(fill="both", expand=True, padx=10, pady=10)

        json_str = json.dumps(
            item,
            indent=2,
            ensure_ascii=False,
            cls=DecimalEncoder
        )
        text.insert("0.0", json_str)
        text.configure(state="disabled")

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
            self.info_text.configure(state="normal")
            self.info_text.delete("0.0", "end")
            self.info_text.insert("0.0", info_text)
            self.info_text.configure(state="disabled")

        except Exception as e:
            self.info_text.configure(state="normal")
            self.info_text.delete("0.0", "end")
            self.info_text.insert("0.0", f"Erro ao carregar info:\n{str(e)}")
            self.info_text.configure(state="disabled")

    def show_import_dialog(self):
        """Show import dialog for importing data to local DynamoDB"""
        if not config.DYNAMODB_LOCAL:
            messagebox.showerror(
                "Erro de Segurança",
                "❌ Importação só é permitida em modo LOCAL!\n\n"
                "Por segurança, esta funcionalidade não funciona quando conectado à produção."
            )
            return

        table_name = None
        if self.selected_table_btn:
            table_name = self.selected_table_btn.cget("text")

        dialog = ImportDialog(self.root, self.db_service, table_name=table_name)

        if dialog and hasattr(dialog, 'result'):
            self.load_tables()
