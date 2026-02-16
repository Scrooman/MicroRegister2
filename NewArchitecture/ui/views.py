"""View Definitions - Ekrany aplikacji"""

class View:
    """Bazowa klasa widoku"""
    
    def __init__(self, name: str):
        self.name = name
    
    def render(self, display, data: dict):
        """
        Renderuj widok na ekranie
        
        Args:
            display: Display driver instance
            data: Dane do wyświetlenia
        """
        pass


class HomeView(View):
    """Ekran główny"""
    
    def __init__(self):
        super().__init__("Home")
    
    def render(self, display, data: dict):
        display.clear()
        display.text("ESP32 App", 30, 0)
        display.text("------------", 20, 10)
        
        # Menu items
        items = data.get('menu_items', [])
        selected = data.get('selected_index', 0)
        
        for i, item in enumerate(items[:4]):  # Max 4 items
            prefix = ">" if i == selected else " "
            display.text(f"{prefix} {item}", 0, 25 + i * 10)
        
        display.show()


class CardReaderView(View):
    """Ekran czytnika kart"""
    
    def __init__(self):
        super().__init__("Card Reader")
    
    def render(self, display, data: dict):
        display.clear()
        display.text("Chip Reader", 25, 0)
        display.text("------------", 20, 10)
        
        if data.get('card_present'):
            # Karta wykryta - pokaż UID i zadanie
            scanned_chips_task_name = data.get('scanned_chips_task_name', 'Unknown Task')
            display.text("Task:", 0, 25)
            display.text(f"{scanned_chips_task_name}", 0, 35)
            # w kolejnej linii wyświetld czas wykrycia karty, jeśli jest dostępny
            scanned_chips_task_start_time = data.get('scanned_chips_task_start_time', 'Unknown Time')
            display.text(f"{scanned_chips_task_start_time}", 0, 47)
        else:
            # Czekaj na kartę
            display.text("Waiting for", 25, 30)
            display.text("Task chip...", 25, 42)
        
        display.show()


class WiFiView(View):
    """Ekran WiFi"""
    
    def __init__(self):
        super().__init__("WiFi")
    
    def render(self, display, data: dict):
        display.clear()
        display.text("WiFi Status", 25, 0)
        display.text("------------", 20, 10)
        
        if data.get('connected'):
            display.text("Connected", 30, 25)
            ssid = data.get('ssid', '')
            if ssid:
                display.text(ssid[:16], 10, 37)
            ip = data.get('ip', '')
            if ip:
                display.text(ip, 10, 49)
        else:
            display.text("Disconnected", 20, 30)
            display.text("Press to", 30, 42)
            display.text("connect", 35, 52)
        
        display.show()


class SettingsView(View):
    """Ekran ustawień"""
    
    def __init__(self):
        super().__init__("Settings")
    
    def render(self, display, data: dict):
        display.clear()
        display.text("Settings", 35, 0)
        display.text("------------", 20, 10)
        
        items = data.get('settings_items', [])
        selected = data.get('selected_index', 0)
        
        for i, item in enumerate(items[:4]):
            prefix = ">" if i == selected else " "
            display.text(f"{prefix} {item}", 0, 25 + i * 10)
        
        display.show()


class CardIdentifierView(View):
    """Widok identyfikacji karty"""

    def __init__(self):
        super().__init__("Auth Card Identifier")
    
    def render(self, display, data):
        display.clear()
        
        # Header
        display.text("Auth Card Identifier", 10, 0)
        display.text("------------", 20, 10)
        
        if data.get('card_uid'):
            # Wyświetl UID karty
            display.text("UID:", 10, 28)
            display.text(data['card_uid'], 10, 42)
        else:
            # Czekaj na kartę
            display.text("Waiting for card...", 10, 35)
        
        display.show()


class KeypadView(View):
    """Widok klawiatury"""
    
    def __init__(self):
        super().__init__("Keypad")
    
    def render(self, display, data):
        display.clear()
        
        # Header
        display.text("Enter PIN", 35, 0)
        display.text("------------", 20, 10)
        
        # Jeśli jest oczekujący UID karty - pokaż info
        pending_uid = data.get('pending_card_uid')
        if pending_uid:
            display.text("Card:", 10, 20)
            if len(pending_uid) <= 12:
                display.text(pending_uid[:12], 45, 20)
            else:
                display.text(pending_uid[:12] + "...", 45, 20)
        
        # Pokaż aktualny bufor
        buffer = data.get('keypad_buffer', '')
        max_len = data.get('keypad_max_length', 4)
        
        # Wyświetl wprowadzony kod
        display.text("PIN:", 10, 35)
        
        # Wyświetl każdą cyfrę osobno (nie zamieniaj na gwiadki)
        for i in range(max_len):
            if i < len(buffer):
                display.text(buffer[i], 45 + i * 10, 35)
            else:
                display.text("_", 45 + i * 10, 35)
        
        # Instrukcja
        if len(buffer) >= max_len:
            display.text("Press to confirm", 15, 57)
        else:
            display.text("Enter digit", 30, 57)
        
        display.show()
