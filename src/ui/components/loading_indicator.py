"""Loading Indicator Component"""

import tkinter as tk


class LoadingIndicator:
    """Indicador de loading com spinner animado"""
    
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, status_label):
        """Initialize LoadingIndicator
        
        Args:
            status_label: Label widget to display status
        """
        self.status_label = status_label
        self.is_loading = False
        self.current_frame = 0
    
    def start(self, message="Carregando..."):
        """Start the loading animation
        
        Args:
            message: Message to display
        """
        self.is_loading = True
        self.current_frame = 0
        self._animate(message)
    
    def _animate(self, message):
        """Animate the spinner
        
        Args:
            message: Message to display
        """
        if self.is_loading:
            spinner = self.SPINNER_FRAMES[self.current_frame]
            self.status_label.config(
                text=f"{spinner} {message}", 
                foreground="blue"
            )
            self.current_frame = (self.current_frame + 1) % len(self.SPINNER_FRAMES)
            self.status_label.after(100, lambda: self._animate(message))
    
    def stop_success(self, message):
        """Stop loading with success status
        
        Args:
            message: Success message to display
        """
        self.is_loading = False
        self.status_label.config(
            text=f"✅ {message}", 
            foreground="green"
        )
    
    def stop_error(self, message):
        """Stop loading with error status
        
        Args:
            message: Error message to display
        """
        self.is_loading = False
        self.status_label.config(
            text=f"❌ {message}", 
            foreground="red"
        )
    
    def stop_warning(self, message):
        """Stop loading with warning status
        
        Args:
            message: Warning message to display
        """
        self.is_loading = False
        self.status_label.config(
            text=f"⚠️ {message}", 
            foreground="orange"
        )
    
    def stop(self):
        """Stop loading animation without changing message"""
        self.is_loading = False