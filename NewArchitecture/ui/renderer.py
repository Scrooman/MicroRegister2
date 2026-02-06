"""Renderer - Engine renderowania"""

class Renderer:
    """Engine renderowania widoków na wyświetlaczu"""
    
    def __init__(self, display_driver):
        """
        Args:
            display_driver: Display driver instance
        """
        self.display = display_driver
        self.current_view = None
        self.view_data = {}
    
    def set_view(self, view):
        """
        Ustaw aktywny widok
        
        Args:
            view: View instance
        """
        self.current_view = view
        print(f"[Renderer] View changed to: {view.name}")
    
    def update_data(self, data: dict):
        """
        Zaktualizuj dane widoku
        
        Args:
            data: Słownik z danymi
        """
        self.view_data.update(data)
    
    def render(self):
        """Renderuj aktualny widok"""
        if self.current_view:
            self.current_view.render(self.display, self.view_data)
    
    def force_render(self):
        """Wymuś natychmiastowe renderowanie"""
        self.render()
