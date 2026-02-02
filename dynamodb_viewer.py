#!/usr/bin/env python3
"""
DynamoDB Viewer - Com Interface de Filtros Visuais
Similar à interface AWS Console
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from decimal import Decimal
from datetime import datetime

class DecimalEncoder(json.JSONEncoder):
    """Encoder para lidar com Decimal do DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

import threading

class LoadingIndicator:
    """Indicador de loading com spinner animado"""
    def __init__(self, status_label):
        self.status_label = status_label
        self.is_loading = False
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_frame = 0
    
    def start(self, message="Carregando..."):
        """Inicia o loading"""
        self.is_loading = True
        self.current_frame = 0
        self._animate(message)
    
    def _animate(self, message):
        """Anima o spinner"""
        if self.is_loading:
            spinner = self.spinner_frames[self.current_frame]
            self.status_label.config(text=f"{spinner} {message}", foreground="blue")
            self.current_frame = (self.current_frame + 1) % len(self.spinner_frames)
            self.status_label.after(100, lambda: self._animate(message))
    
    def stop_success(self, message):
        """Para o loading com sucesso"""
        self.is_loading = False
        self.status_label.config(text=f"✅ {message}", foreground="green")
    
    def stop_error(self, message):
        """Para o loading com erro"""
        self.is_loading = False
        self.status_label.config(text=f"❌ {message}", foreground="red")
    
    def stop_warning(self, message):
        """Para o loading com aviso"""
        self.is_loading = False
        self.status_label.config(text=f"⚠️ {message}", foreground="orange")

class FilterRow:
    """Classe para representar uma linha de filtro"""
    def __init__(self, parent, on_remove, attributes=None):
        self.frame = ttk.Frame(parent)
        self.on_remove = on_remove
        self.attributes = attributes or []
        
        # Nome do atributo
        self.attr_var = tk.StringVar()
        self.attr_combo = ttk.Combobox(self.frame, textvariable=self.attr_var, 
                                       values=self.attributes, width=20)
        self.attr_combo.grid(row=0, column=0, padx=5, pady=5)
        
        # Condição
        self.condition_var = tk.StringVar(value="Igual a")
        self.condition_combo = ttk.Combobox(self.frame, textvariable=self.condition_var,
                                           values=[
                                               "Igual a",
                                               "Diferente de",
                                               "Menor que ou igual a",
                                               "Menor que",
                                               "Maior que ou igual a",
                                               "Maior que",
                                               "Contém",
                                               "Começa com",
                                               "Entre",
                                               "Existe",
                                               "Não existe"
                                           ], width=20, state="readonly")
        self.condition_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Tipo
        self.type_var = tk.StringVar(value="String")
        self.type_combo = ttk.Combobox(self.frame, textvariable=self.type_var,
                                      values=["String", "Number", "Boolean"],
                                      width=15, state="readonly")
        self.type_combo.grid(row=0, column=2, padx=5, pady=5)
        
        # Valor
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(self.frame, textvariable=self.value_var, width=30)
        self.value_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Botão remover
        self.remove_btn = ttk.Button(self.frame, text="✕", width=3, 
                                     command=self.remove)
        self.remove_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Bind para esconder valor quando seleciona "Existe" ou "Não existe"
        self.condition_combo.bind('<<ComboboxSelected>>', self.on_condition_change)
    
    def on_condition_change(self, event=None):
        """Esconde campo valor para condições que não precisam"""
        condition = self.condition_var.get()
        if condition in ["Existe", "Não existe"]:
            self.value_entry.config(state='disabled')
            self.type_combo.config(state='disabled')
        else:
            self.value_entry.config(state='normal')
            self.type_combo.config(state='normal')
    
    def pack(self):
        self.frame.pack(fill=tk.X, padx=5, pady=2)
    
    def remove(self):
        self.frame.destroy()
        self.on_remove(self)
    
    def get_filter(self):
        """Retorna o filtro configurado"""
        attr = self.attr_var.get().strip()
        condition = self.condition_var.get()
        value_type = self.type_var.get()
        value = self.value_var.get().strip()
        
        if not attr:
            return None
        
        # Converte valor para tipo apropriado
        if condition not in ["Existe", "Não existe"]:
            if not value:
                return None
            
            if value_type == "Number":
                try:
                    value = float(value)
                except ValueError:
                    return None
            elif value_type == "Boolean":
                value = value.lower() in ['true', '1', 'sim', 'yes']
        
        return {
            'attribute': attr,
            'condition': condition,
            'type': value_type,
            'value': value
        }

class DynamoDBViewerV2:
    def __init__(self, root):
        self.root = root
        self.root.title("DynamoDB Viewer")
        self.root.geometry("1400x800")
        
        # Cliente DynamoDB
        self.dynamodb = None
        self.current_table = None
        self.current_items = []
        self.filter_rows = []
        self.all_attributes = []
        
        self.setup_ui()
        self.connect_to_dynamodb()
        # Inicializa o indicador de loading (CORRIGIDO)
        self.loading_indicator = LoadingIndicator(self.status_label)
        
    def setup_ui(self):
        """Configura a interface do usuário"""
        # Frame principal dividido em 3 partes
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Painel esquerdo - Lista de tabelas
        left_frame = ttk.Frame(main_paned, width=200)
        main_paned.add(left_frame, weight=1)
        
        # Painel direito
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=4)
        
        self.setup_left_panel(left_frame)
        self.setup_right_panel(right_frame)
        
    def setup_left_panel(self, parent):
        """Painel com lista de tabelas"""
        ttk.Label(parent, text="Tabelas DynamoDB", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Botão refresh
        ttk.Button(parent, text="🔄 Atualizar", command=self.load_tables).pack(pady=5, fill=tk.X, padx=5)
        
        # Frame para lista de tabelas
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox de tabelas
        self.tables_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.tables_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tables_listbox.yview)
        
        self.tables_listbox.bind('<<ListboxSelect>>', self.on_table_select)
        
        # Info de conexão
        self.connection_label = ttk.Label(parent, text="Desconectado", foreground="red")
        self.connection_label.pack(pady=5)
        
    def setup_right_panel(self, parent):
        """Painel com dados e filtros"""
        # Notebook para abas
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba 1: Dados da tabela com filtros
        self.data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_frame, text="📊 Dados com Filtros")
        self.setup_data_with_filters_tab(self.data_frame)
        
        # Aba 2: Info da tabela
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="ℹ️ Info")
        self.setup_info_tab(self.info_frame)
        
    def setup_data_with_filters_tab(self, parent):
        """Aba de visualização de dados com filtros visuais"""
        # Frame de filtros
        filters_frame = ttk.LabelFrame(parent, text="▼ Filtros - opcional")
        filters_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Container para as linhas de filtro
        self.filters_container = ttk.Frame(filters_frame)
        self.filters_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Botões de ação dos filtros
        filter_actions = ttk.Frame(filters_frame)
        filter_actions.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(filter_actions, text="➕ Adicionar filtro", 
                  command=self.add_filter_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_actions, text="▶ Executar", 
                  command=self.execute_filters, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_actions, text="🔄 Redefinir", 
                  command=self.reset_filters).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(filter_actions, text="")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Separator
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
        
        # Toolbar de dados
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="📥 Carregar Tudo", 
                  command=self.load_all_data).pack(side=tk.LEFT, padx=2)
        
        self.limit_label = ttk.Label(toolbar, text="Limite:")
        self.limit_label.pack(side=tk.LEFT, padx=5)
        
        self.limit_var = tk.StringVar(value="100")
        limit_spinbox = ttk.Spinbox(toolbar, from_=10, to=1000, 
                                   textvariable=self.limit_var, width=10)
        limit_spinbox.pack(side=tk.LEFT)
        
        self.count_label = ttk.Label(toolbar, text="Items: 0")
        self.count_label.pack(side=tk.RIGHT, padx=5)
        
        # Frame para treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        self.data_tree = ttk.Treeview(tree_frame, 
                                      yscrollcommand=vsb.set, 
                                      xscrollcommand=hsb.set)
        vsb.config(command=self.data_tree.yview)
        hsb.config(command=self.data_tree.xview)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.data_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind para double-click
        self.data_tree.bind('<Double-1>', self.show_item_details)
        
    def setup_info_tab(self, parent):
        """Aba com informações da tabela"""
        self.info_text = scrolledtext.ScrolledText(parent, height=20)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def connect_to_dynamodb(self):
        """Conecta ao DynamoDB usando credenciais do AWS CLI"""
        try:
            self.dynamodb = boto3.resource('dynamodb')
            list(self.dynamodb.tables.limit(1))
            self.connection_label.config(text="✓ Conectado", foreground="green")
            self.load_tables()
        except Exception as e:
            self.connection_label.config(text="✗ Erro de conexão", foreground="red")
            messagebox.showerror("Erro de Conexão", 
                               f"Erro ao conectar ao DynamoDB:\n{str(e)}\n\n"
                               "Configure o AWS CLI com: aws configure")
    
    def load_tables(self):
        """Carrega lista de tabelas"""
        if not self.dynamodb:
            return
            
        try:
            self.tables_listbox.delete(0, tk.END)
            tables = list(self.dynamodb.tables.all())
            
            for table in tables:
                self.tables_listbox.insert(tk.END, table.name)
                
            if not tables:
                messagebox.showinfo("Info", "Nenhuma tabela encontrada no DynamoDB")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar tabelas:\n{str(e)}")
    
    def on_table_select(self, event):
        """Callback quando uma tabela é selecionada"""
        selection = self.tables_listbox.curselection()
        if selection:
            table_name = self.tables_listbox.get(selection[0])
            self.current_table = self.dynamodb.Table(table_name)
            self.show_table_info()
            self.load_table_attributes()
            self.reset_filters()
    
    def load_table_attributes(self):
        """Carrega atributos da tabela para usar nos filtros"""
        if not self.current_table:
            return
        
        try:
            # Faz um scan de poucos items para pegar os atributos
            response = self.current_table.scan(Limit=10)
            items = response['Items']
            
            # Coleta todos os atributos únicos
            all_keys = set()
            for item in items:
                all_keys.update(item.keys())
            
            self.all_attributes = sorted(list(all_keys))
            
        except Exception as e:
            print(f"Erro ao carregar atributos: {e}")
            self.all_attributes = []
    
    def add_filter_row(self):
        """Adiciona uma nova linha de filtro"""
        filter_row = FilterRow(self.filters_container, self.remove_filter_row, 
                              self.all_attributes)
        filter_row.pack()
        self.filter_rows.append(filter_row)
    
    def remove_filter_row(self, row):
        """Remove uma linha de filtro"""
        if row in self.filter_rows:
            self.filter_rows.remove(row)
    
    def reset_filters(self):
        """Remove todos os filtros"""
        for row in self.filter_rows[:]:
            row.remove()
        self.filter_rows = []
        self.status_label.config(text="")
    
    def build_filter_expression(self):
        """Constrói a FilterExpression do DynamoDB a partir dos filtros visuais"""
        filters = []
        
        for row in self.filter_rows:
            filter_data = row.get_filter()
            if not filter_data:
                continue
            
            attr = filter_data['attribute']
            condition = filter_data['condition']
            value = filter_data['value']
            
            # Constrói a condição usando boto3.dynamodb.conditions
            if condition == "Igual a":
                filters.append(Attr(attr).eq(value))
            elif condition == "Diferente de":
                filters.append(Attr(attr).ne(value))
            elif condition == "Menor que":
                filters.append(Attr(attr).lt(value))
            elif condition == "Menor que ou igual a":
                filters.append(Attr(attr).lte(value))
            elif condition == "Maior que":
                filters.append(Attr(attr).gt(value))
            elif condition == "Maior que ou igual a":
                filters.append(Attr(attr).gte(value))
            elif condition == "Contém":
                filters.append(Attr(attr).contains(value))
            elif condition == "Começa com":
                filters.append(Attr(attr).begins_with(value))
            elif condition == "Existe":
                filters.append(Attr(attr).exists())
            elif condition == "Não existe":
                filters.append(Attr(attr).not_exists())
        
        # Combina todos os filtros com AND
        if not filters:
            return None
        
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
        
        return combined_filter
    
    def execute_filters(self):
        """Executa o scan com os filtros aplicados (com paginação se necessário)"""
        if not self.current_table:
            messagebox.showwarning("Aviso", "Selecione uma tabela primeiro")
            return
        # Inicia o loading em thread separada
        thread = threading.Thread(target=self._do_execute_filters, daemon=True)
        thread.start()

    def _do_execute_filters(self):
        """Executa o filtro em thread separada"""
        try:
            self.loading_indicator.start("Carregando dados...")

            limit = int(self.limit_var.get())
            filter_expr = self.build_filter_expression()

            # Recolhe filtros brutos para possível atalho por chave primária
            raw_filters = [r.get_filter() for r in self.filter_rows if r.get_filter()]

            items = []
            scanned_count = 0

            # Verifica se podemos usar atalho por chave primária (get_item ou query)
            use_pk_shortcut = False
            pk_key = None
            sk_key = None
            pk_value = None
            sk_value = None
            try:
                key_schema = getattr(self.current_table, 'key_schema', None)
                if key_schema:
                    for k in key_schema:
                        if k.get('KeyType') == 'HASH':
                            pk_key = k.get('AttributeName')
                        elif k.get('KeyType') == 'RANGE':
                            sk_key = k.get('AttributeName')

                # Detecta equality filters on PK/SK
                for f in raw_filters:
                    if not f:
                        continue
                    if f['condition'] == 'Igual a':
                        if f['attribute'] == pk_key:
                            pk_value = f['value']
                        if sk_key and f['attribute'] == sk_key:
                            sk_value = f['value']

                if pk_key and pk_value is not None:
                    # podemos usar atalho (get_item se tiver SK também)
                    use_pk_shortcut = True
            except Exception:
                use_pk_shortcut = False

            if use_pk_shortcut:
                # Se temos tanto PK quanto SK -> get_item
                if pk_value is not None and sk_key and sk_value is not None:
                    try:
                        key = {pk_key: pk_value, sk_key: sk_value}
                        resp = self.current_table.get_item(Key=key)
                        item = resp.get('Item')
                        if item:
                            items = [item]
                            scanned_count = 1
                        else:
                            items = []
                            scanned_count = 0
                    except Exception as e:
                        raise
                else:
                    # Apenas PK -> query para todos os items da partição (pode retornar muitos)
                    try:
                        q_kwargs = {'KeyConditionExpression': Key(pk_key).eq(pk_value), 'Limit': limit}
                        resp = self.current_table.query(**q_kwargs)
                        items = resp.get('Items', [])
                        scanned_count = resp.get('ScannedCount', len(items))
                    except Exception:
                        # falha no atalho, cai para scan completo
                        use_pk_shortcut = False

            # Se não usamos atalho, faz scan paginado com streaming
            if not use_pk_shortcut:
                page_size = 1000
                batch_update = 50
                self.loading_indicator.start("Filtrando dados em toda a tabela...")
                # Usa Table.scan com paginação manual (aceita Attr expressions)
                last_evaluated_key = None
                while True:
                    scan_kwargs = {'Limit': page_size}
                    if filter_expr is not None:
                        scan_kwargs['FilterExpression'] = filter_expr
                    if last_evaluated_key:
                        scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

                    page = self.current_table.scan(**scan_kwargs)
                    page_items = page.get('Items', [])
                    scanned_count += page.get('ScannedCount', 0)

                    # Converte e adiciona
                    page_items_py = json.loads(json.dumps(page_items, cls=DecimalEncoder))
                    items.extend(page_items_py)

                    # Atualiza a UI em batches para dar sensação de streaming
                    if len(items) >= batch_update:
                        current_snapshot = items[:min(len(items), limit)]
                        self.root.after(0, lambda snap=current_snapshot: self.display_items(snap))
                        self.root.after(0, lambda cnt=len(current_snapshot): self.count_label.config(text=f"Items: {cnt}"))
                        self.loading_indicator.start(f"Processado: {len(items)} items verificados...")

                    if len(items) >= limit:
                        items = items[:limit]
                        break

                    last_evaluated_key = page.get('LastEvaluatedKey')
                    if not last_evaluated_key:
                        break

            # Converte Decimals caso tenhamos vindo do atalho
            items = json.loads(json.dumps(items, cls=DecimalEncoder))

            self.current_items = items
            # Atualiza UI final
            self.root.after(0, lambda: self.display_items(items))
            mensagem = f"Items devolvidos: {len(items)} | Items verificados: {scanned_count}"
            self.root.after(0, lambda: self.count_label.config(text=f"Items: {len(items)}"))
            self.root.after(0, lambda: self.loading_indicator.stop_success(mensagem))

        except Exception as e:
            erro_msg = f"Erro ao executar filtros: {str(e)}"
            self.root.after(0, lambda: self.loading_indicator.stop_error(erro_msg))
            self.root.after(0, lambda: messagebox.showerror("Erro", erro_msg))
            import traceback
            print(traceback.format_exc())
    
    def load_all_data(self):
        """Carrega dados sem filtros"""
        self.reset_filters()
        self.execute_filters()
    
    def display_items(self, items):
        """Exibe items no treeview"""
        # Limpa treeview
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        if not items:
            self.data_tree["columns"] = []
            return
        
        # Obtém todas as colunas dos items
        all_keys = set()
        for item in items:
            all_keys.update(item.keys())
        
        columns = sorted(list(all_keys))
        
        # Configura colunas
        self.data_tree["columns"] = columns
        self.data_tree["show"] = "headings"
        
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=150)
        
        # Adiciona items
        for item in items:
            values = []
            for col in columns:
                value = item.get(col, "")
                if isinstance(value, Decimal):
                    value = float(value)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)[:50] + "..."
                values.append(str(value))
            
            self.data_tree.insert("", tk.END, values=values)
    
    def show_item_details(self, event):
        """Mostra detalhes do item em uma janela popup"""
        selection = self.data_tree.selection()
        if not selection:
            return
        
        item_index = self.data_tree.index(selection[0])
        if item_index >= len(self.current_items):
            return
        
        item = self.current_items[item_index]
        
        # Cria janela popup
        popup = tk.Toplevel(self.root)
        popup.title("Detalhes do Item")
        popup.geometry("600x400")
        
        text = scrolledtext.ScrolledText(popup)
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Exibe JSON formatado
        json_str = json.dumps(item, indent=2, ensure_ascii=False, cls=DecimalEncoder)
        text.insert(1.0, json_str)
        text.config(state=tk.DISABLED)
    
    def show_table_info(self):
        """Mostra informações da tabela"""
        if not self.current_table:
            return
        
        try:
            self.current_table.reload()
            
            info = {
                "Nome": self.current_table.name,
                "Status": self.current_table.table_status,
                "Item Count": self.current_table.item_count,
                "Tamanho (bytes)": self.current_table.table_size_bytes,
                "Criação": str(self.current_table.creation_date_time),
                "Chave Primária": self.current_table.key_schema,
                "Atributos": self.current_table.attribute_definitions,
                "Global Secondary Indexes": self.current_table.global_secondary_indexes or "Nenhum",
                "Local Secondary Indexes": self.current_table.local_secondary_indexes or "Nenhum",
            }
            
            info_text = json.dumps(info, indent=2, ensure_ascii=False, default=str)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            
        except Exception as e:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, f"Erro ao carregar info:\n{str(e)}")

def main():
    root = tk.Tk()
    app = DynamoDBViewerV2(root)
    root.mainloop()

if __name__ == "__main__":
    main()