"""Filter Row Model"""

import tkinter as tk
from tkinter import ttk
from decimal import Decimal


class FilterRow:
    """Classe para representar uma linha de filtro"""
    
    CONDITIONS = [
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
    ]
    
    TYPES = ["String", "Number", "Boolean"]
    
    def __init__(self, parent, on_remove, attributes=None):
        """Initialize FilterRow
        
        Args:
            parent: Parent widget
            on_remove: Callback function when row is removed
            attributes: List of available attributes for filtering
        """
        self.frame = ttk.Frame(parent)
        self.on_remove = on_remove
        self.attributes = attributes or []
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create and layout widgets"""
        # Nome do atributo
        self.attr_var = tk.StringVar()
        self.attr_combo = ttk.Combobox(
            self.frame, 
            textvariable=self.attr_var, 
            values=self.attributes, 
            width=20
        )
        self.attr_combo.grid(row=0, column=0, padx=5, pady=5)
        
        # Condição
        self.condition_var = tk.StringVar(value="Igual a")
        self.condition_combo = ttk.Combobox(
            self.frame, 
            textvariable=self.condition_var,
            values=self.CONDITIONS, 
            width=20, 
            state="readonly"
        )
        self.condition_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Tipo
        self.type_var = tk.StringVar(value="String")
        self.type_combo = ttk.Combobox(
            self.frame, 
            textvariable=self.type_var,
            values=self.TYPES,
            width=15, 
            state="readonly"
        )
        self.type_combo.grid(row=0, column=2, padx=5, pady=5)
        
        # Valor
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(
            self.frame, 
            textvariable=self.value_var, 
            width=30
        )
        self.value_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Botão remover
        self.remove_btn = ttk.Button(
            self.frame, 
            text="✕", 
            width=3, 
            command=self.remove
        )
        self.remove_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Bind para esconder valor quando seleciona "Existe" ou "Não existe"
        self.condition_combo.bind('<<ComboboxSelected>>', self.on_condition_change)
    
    def on_condition_change(self, event=None):
        """Handle condition change - hide value for conditions that don't need it"""
        condition = self.condition_var.get()
        if condition in ["Existe", "Não existe"]:
            self.value_entry.config(state='disabled')
            self.type_combo.config(state='disabled')
        else:
            self.value_entry.config(state='normal')
            self.type_combo.config(state='normal')
    
    def pack(self):
        """Pack the frame"""
        self.frame.pack(fill=tk.X, padx=5, pady=2)
    
    def remove(self):
        """Remove this filter row"""
        self.frame.destroy()
        self.on_remove(self)
    
    def get_filter(self):
        """Return the configured filter or None if invalid
        
        Returns:
            dict or None: Filter configuration with keys: attribute, condition, type, value
        """
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
                    # Convert to Decimal (same type used by DynamoDB/boto3)
                    value = Decimal(value)
                except Exception:
                    return None
            elif value_type == "Boolean":
                value = value.lower() in ['true', '1', 'sim', 'yes']
        
        return {
            'attribute': attr,
            'condition': condition,
            'type': value_type,
            'value': value
        }
