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
        display.text("NFC Reader", 25, 0)
        display.text("------------", 20, 10)
        
        if data.get('card_present'):
            # Karta wykryta
            uid = data.get('card_uid', 'Unknown')
            display.text("Card:", 0, 25)
            if len(uid) <= 16:
                display.text(uid, 0, 35)
            else:
                display.text(uid[:16], 0, 35)
                display.text(uid[16:], 0, 45)
            
            scanned = data.get('cards_scanned', 0)
            display.text(f"Total: {scanned}", 0, 55)
        else:
            # Czekaj na kartę
            display.text("Waiting for", 25, 30)
            display.text("NFC card...", 25, 42)
        
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
        super().__init__("Card Identifier")
    
    def render(self, display, data):
        display.clear()
        
        # Header
        display.text("Card Identifier", 10, 0)
        display.text("------------", 20, 10)
        
        if data.get('card_uid'):
            # Wyświetl UID karty
            display.text("UID:", 10, 28)
            display.text(data['card_uid'], 10, 42)
        else:
            # Czekaj na kartę
            display.text("Waiting for card...", 10, 35)
        
        display.show()
