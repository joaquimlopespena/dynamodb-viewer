#!/usr/bin/env python3
"""
DynamoDB Viewer - Aplicativo Desktop para visualizar dados do DynamoDB
Similar ao HeidiSQL para bancos relacionais
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

class DynamoDBViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("DynamoDB Viewer")
        self.root.geometry("1200x700")
        
        # Cliente DynamoDB
        self.dynamodb = None
        self.current_table = None
        self.current_items = []
        
        self.setup_ui()
        self.connect_to_dynamodb()
        
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
        """Painel com dados e queries"""
        # Notebook para abas
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Aba 1: Dados da tabela
        self.data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_frame, text="📊 Dados")
        self.setup_data_tab(self.data_frame)
        
        # Aba 2: Query/Scan
        self.query_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.query_frame, text="🔍 Query")
        self.setup_query_tab(self.query_frame)
        
        # Aba 3: Info da tabela
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="ℹ️ Info")
        self.setup_info_tab(self.info_frame)
        
    def setup_data_tab(self, parent):
        """Aba de visualização de dados"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="📥 Carregar Dados", command=self.load_table_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_data).pack(side=tk.LEFT, padx=2)
        
        self.limit_label = ttk.Label(toolbar, text="Limite:")
        self.limit_label.pack(side=tk.LEFT, padx=5)
        
        self.limit_var = tk.StringVar(value="100")
        limit_spinbox = ttk.Spinbox(toolbar, from_=10, to=1000, textvariable=self.limit_var, width=10)
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
        
    def setup_query_tab(self, parent):
        """Aba para queries customizadas"""
        # Frame superior - input de query
        query_input_frame = ttk.LabelFrame(parent, text="Query/Scan")
        query_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Tipo de operação
        op_frame = ttk.Frame(query_input_frame)
        op_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(op_frame, text="Operação:").pack(side=tk.LEFT)
        self.operation_var = tk.StringVar(value="scan")
        ttk.Radiobutton(op_frame, text="Scan", variable=self.operation_var, value="scan").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(op_frame, text="Query", variable=self.operation_var, value="query").pack(side=tk.LEFT, padx=5)
        
        # Filter Expression
        ttk.Label(query_input_frame, text="Filter Expression (opcional):").pack(anchor=tk.W, padx=5)
        self.filter_entry = ttk.Entry(query_input_frame, width=80)
        self.filter_entry.pack(fill=tk.X, padx=5, pady=2)
        
        # Key Condition (para Query)
        ttk.Label(query_input_frame, text="Key Condition (para Query):").pack(anchor=tk.W, padx=5)
        self.key_condition_entry = ttk.Entry(query_input_frame, width=80)
        self.key_condition_entry.pack(fill=tk.X, padx=5, pady=2)
        
        # Botão executar
        ttk.Button(query_input_frame, text="▶ Executar", command=self.execute_query).pack(pady=5)
        
        # Resultado
        result_frame = ttk.LabelFrame(parent, text="Resultado")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.query_result_text = scrolledtext.ScrolledText(result_frame, height=20)
        self.query_result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_info_tab(self, parent):
        """Aba com informações da tabela"""
        self.info_text = scrolledtext.ScrolledText(parent, height=20)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def connect_to_dynamodb(self):
        """Conecta ao DynamoDB usando credenciais do AWS CLI"""
        try:
            # Tenta usar as credenciais configuradas no AWS CLI
            self.dynamodb = boto3.resource('dynamodb')
            # Testa a conexão
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
            self.load_table_data()
    
    def load_table_data(self):
        """Carrega dados da tabela selecionada"""
        if not self.current_table:
            messagebox.showwarning("Aviso", "Selecione uma tabela primeiro")
            return
        
        try:
            limit = int(self.limit_var.get())
            response = self.current_table.scan(Limit=limit)
            self.current_items = response['Items']
            
            # Converte Decimals para garantir compatibilidade
            self.current_items = json.loads(
                json.dumps(self.current_items, cls=DecimalEncoder)
            )
            
            self.display_items(self.current_items)
            self.count_label.config(text=f"Items: {len(self.current_items)}")
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            messagebox.showerror("Erro", 
                f"Erro ao carregar dados:\n{str(e)}\n\n"
                f"Detalhes:\n{error_detail[:500]}")
            print(f"Erro completo:\n{error_detail}")
    
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
                # Converte Decimal para float primeiro
                if isinstance(value, Decimal):
                    value = float(value)
                # Converte para string de forma legível
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, cls=DecimalEncoder)[:50] + "..."
                values.append(str(value))
            
            self.data_tree.insert("", tk.END, values=values)
    
    def refresh_data(self):
        """Atualiza os dados"""
        self.load_table_data()
    
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
    
    def execute_query(self):
        """Executa query/scan customizado"""
        if not self.current_table:
            messagebox.showwarning("Aviso", "Selecione uma tabela primeiro")
            return
        
        try:
            operation = self.operation_var.get()
            filter_expr = self.filter_entry.get().strip()
            key_condition = self.key_condition_entry.get().strip()
            limit = int(self.limit_var.get())
            
            if operation == "scan":
                # Scan com ou sem filtro
                scan_kwargs = {'Limit': limit}
                
                # Adiciona filtro se fornecido
                if filter_expr:
                    # Tenta usar o filtro como FilterExpression
                    # Exemplos aceitos:
                    # - attribute_exists(campo)
                    # - contains(campo, valor)
                    # - campo = valor
                    try:
                        scan_kwargs['FilterExpression'] = filter_expr
                        response = self.current_table.scan(**scan_kwargs)
                    except Exception as e:
                        messagebox.showerror("Erro no Filtro", 
                            f"Filtro inválido: {str(e)}\n\n"
                            "Exemplos de filtros válidos:\n"
                            "- attribute_exists(email)\n"
                            "- contains(#n, :val) -- requer ExpressionAttributeNames/Values\n"
                            "- campo = :val -- requer ExpressionAttributeValues")
                        return
                else:
                    response = self.current_table.scan(**scan_kwargs)
                
                items = response['Items']
                
            else:  # query
                if not key_condition:
                    messagebox.showwarning("Aviso", 
                        "Para Query, forneça uma Key Condition\n\n"
                        "Exemplo: userId = :id\n"
                        "(Requer valores adicionais)")
                    return
                
                # Query básico (simplificado)
                messagebox.showinfo("Info", 
                    "Query avançado requer configuração adicional.\n\n"
                    "Para queries complexas, use boto3 diretamente:\n"
                    "table.query(KeyConditionExpression=Key('pk').eq('valor'))")
                return
            
            # Exibe resultado
            result_json = json.dumps(items, indent=2, ensure_ascii=False, cls=DecimalEncoder)
            self.query_result_text.delete(1.0, tk.END)
            self.query_result_text.insert(1.0, 
                f"Operação: {operation.upper()}\n"
                f"Filtro: {filter_expr if filter_expr else 'Nenhum'}\n"
                f"Encontrados: {len(items)} items\n\n"
                f"{result_json}")
            
            if response.get('LastEvaluatedKey'):
                self.query_result_text.insert(tk.END, 
                    "\n\n⚠️ HÁ MAIS RESULTADOS - Aumente o limite para ver mais")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar query:\n{str(e)}")
    
    def show_table_info(self):
        """Mostra informações da tabela"""
        if not self.current_table:
            return
        
        try:
            # Carrega metadados da tabela
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
    app = DynamoDBViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()