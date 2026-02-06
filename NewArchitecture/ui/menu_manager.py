"""Menu Manager - Kontroler menu i nawigacji"""

class MenuManager:
    """Manager menu - kontroluje nawigację i stan menu"""
    
    def __init__(self, renderer):
        """
        Args:
            renderer: Renderer instance
        """
        self.renderer = renderer
        self.current_view = None
        self.menu_items = []
        self.current_index = 0
        self.in_submenu = False
    
    def set_menu_items(self, items: list):
        """
        Ustaw elementy menu
        
        Args:
            items: Lista nazw menu
        """
        self.menu_items = items
        self.current_index = 0
    
    def navigate_next(self):
        """Przejdź do następnego elementu menu"""
        if self.menu_items:
            self.current_index = (self.current_index + 1) % len(self.menu_items)
            print(f"[Menu] Selected: {self.menu_items[self.current_index]}")
    
    def navigate_prev(self):
        """Przejdź do poprzedniego elementu menu"""
        if self.menu_items:
            self.current_index = (self.current_index - 1) % len(self.menu_items)
            print(f"[Menu] Selected: {self.menu_items[self.current_index]}")
    
    def get_selected_item(self) -> str:
        """Pobierz aktualnie wybrany element menu"""
        if self.menu_items and 0 <= self.current_index < len(self.menu_items):
            return self.menu_items[self.current_index]
        return None
    
    def get_selected_index(self) -> int:
        """Pobierz indeks wybranego elementu"""
        return self.current_index
    
    def enter_submenu(self):
        """Wejdź do podmenu"""
        self.in_submenu = True
        selected = self.get_selected_item()
        print(f"[Menu] Entering: {selected}")
    
    def exit_submenu(self):
        """Wyjdź z podmenu"""
        self.in_submenu = False
        print("[Menu] Back to main menu")
    
    def is_in_submenu(self) -> bool:
        """Sprawdź czy jesteśmy w podmenu"""
        return self.in_submenu
