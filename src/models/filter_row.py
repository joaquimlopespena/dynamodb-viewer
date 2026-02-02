"""Filter Row Model"""

import customtkinter as ctk
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
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.on_remove = on_remove
        self.attributes = attributes or []

        self._create_widgets()

    def _create_widgets(self):
        """Create and layout widgets"""
        # Nome do atributo
        self.attr_var = ctk.StringVar()
        self.attr_combo = ctk.CTkComboBox(
            self.frame,
            variable=self.attr_var,
            values=self.attributes if self.attributes else [""],
            width=180,
            height=26
        )
        self.attr_combo.grid(row=0, column=0, padx=4, pady=3)
        self.attr_combo.set("")

        # Condição
        self.condition_var = ctk.StringVar(value="Igual a")
        self.condition_combo = ctk.CTkComboBox(
            self.frame,
            variable=self.condition_var,
            values=self.CONDITIONS,
            width=160,
            height=26,
            state="readonly",
            command=self.on_condition_change
        )
        self.condition_combo.grid(row=0, column=1, padx=4, pady=3)

        # Tipo
        self.type_var = ctk.StringVar(value="String")
        self.type_combo = ctk.CTkComboBox(
            self.frame,
            variable=self.type_var,
            values=self.TYPES,
            width=100,
            height=26,
            state="readonly"
        )
        self.type_combo.grid(row=0, column=2, padx=4, pady=3)

        # Valor
        self.value_var = ctk.StringVar()
        self.value_entry = ctk.CTkEntry(
            self.frame,
            textvariable=self.value_var,
            width=200,
            height=26
        )
        self.value_entry.grid(row=0, column=3, padx=4, pady=3)

        # Botão remover
        self.remove_btn = ctk.CTkButton(
            self.frame,
            text="✕",
            width=32,
            height=26,
            command=self.remove,
            fg_color="#8b0000",
            hover_color="#a52a2a"
        )
        self.remove_btn.grid(row=0, column=4, padx=4, pady=3)

    def on_condition_change(self, value=None):
        """Handle condition change - hide value for conditions that don't need it"""
        condition = self.condition_var.get()
        if condition in ["Existe", "Não existe"]:
            self.value_entry.configure(state='disabled')
            self.type_combo.configure(state='disabled')
        else:
            self.value_entry.configure(state='normal')
            self.type_combo.configure(state='readonly')

    def pack(self):
        """Pack the frame"""
        self.frame.pack(fill="x", padx=4, pady=1)

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
