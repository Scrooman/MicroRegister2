"""
Main Application - ESP32 
Centralna klasa App z Dependency Injection
"""

import uasyncio as asyncio # type: ignore
import time
from config import Config

# Warstwa 1: Drivers
from drivers.encoder import Encoder
from drivers.button import Button
from drivers.led import LED
from drivers.display_driver import Display
from drivers.nfc_reader import NFCReader

# Warstwa 2: Services
from services.storage_manager import StorageManager
from services.network_manager import NetworkManager
from services.auth_manager import AuthManager
from services.task_manager import TaskManager

# Warstwa 3: UI
from ui.views import HomeView, CardReaderView, WiFiView, SettingsView, CardIdentifierView
from ui.menu_manager import MenuManager
from ui.renderer import Renderer


class App:
    """Centralna klasa aplikacji z Dependency Injection"""
    
    def __init__(self, config):
        self.config = config
        
        # Warstwa 1: Hardware Drivers (init in setup)
        self.encoder = None
        self.button = None
        self.led = None
        self.display = None
        self.nfc_reader = None
        
        # Warstwa 2: Services
        self.storage = StorageManager()
        self.network = NetworkManager(config.SERVER_URL)
        self.auth = AuthManager(self.storage, self.network)
        self.tasks = TaskManager()
        
        # Warstwa 3: UI
        self.renderer = None
        self.menu = None
        self.views = {}
        
        # Stan aplikacji (shared state)
        self.state = {
            'current_mode': 'home',  # home, card_reader, card_identifier, wifi, settings
            'card_present': False,
            'card_uid': None,
            'cards_scanned': 0,
            'wifi_connected': False,
            'last_update': 0
        }
    
    def setup(self):
        """Inicjalizacja aplikacji"""
        print("\n" + "="*50)
        print("  ESP32 Application - Layered Architecture")
        print("="*50)
        
        # Setup Hardware Drivers
        print("[Setup] Initializing hardware...")
        self._setup_hardware()
        
        # Setup UI
        print("[Setup] Initializing UI...")
        self._setup_ui()
        
        # Connect WiFi
        if self.config.AUTO_CONNECT_WIFI:
            print("[Setup] Connecting to WiFi...")
            self.network.connect_wifi(
                self.config.WIFI_SSID,
                self.config.WIFI_PASSWORD
            )
            self.state['wifi_connected'] = self.network.is_connected()
        
        print("[Setup] Ready!")
        print("="*50 + "\n")
    
    def _setup_hardware(self):
        """Setup hardware drivers"""
        cfg = self.config
        
        # LED
        self.led = LED(cfg.LED_PIN)
        self.led.blink(times=2, delay_ms=100)
        
        # Display
        self.display = Display(cfg.OLED_SCL, cfg.OLED_SDA)
        self.display.text("Initializing...", 10, 25)
        self.display.show()
        
        # Encoder
        self.encoder = Encoder(
            cfg.ENC_CLK,
            cfg.ENC_DT,
            min_val=0,
            max_val=4,  # 5 menu items
            wrap=True
        )
        
        # Button
        self.button = Button(cfg.ENC_SW)
        
        # NFC Reader
        self.nfc_reader = NFCReader(cfg.NFC_SCL, cfg.NFC_SDA)
    
    def _setup_ui(self):
        """Setup UI layer"""
        # Renderer
        self.renderer = Renderer(self.display)
        
        # Views
        self.views = {
            'home': HomeView(),
            'card_reader': CardReaderView(),
            'card_identifier': CardIdentifierView(),
            'wifi': WiFiView(),
            'settings': SettingsView()
        }
        
        # Menu Manager
        self.menu = MenuManager(self.renderer)
        self.menu.set_menu_items(['Card Reader', 'Card Identifier', 'WiFi', 'Settings', 'About'])
        
        # Set initial view
        self.renderer.set_view(self.views['home'])
    
    async def nfc_scan_task(self):
        """Task: Skanowanie NFC (async)"""
        print("[Task] NFC scan task started")
        
        card_removed_time = None  # Czas odjęcia karty
        
        while True:
            if self.state['current_mode'] == 'card_reader' or self.state['current_mode'] == 'card_identifier':
                # Skanuj tylko w trybie card_reader lub card_identifier
                card = self.nfc_reader.read_card(timeout=0.3)
                
                if card and card['is_new']:
                    # Nowa karta!
                    self.state['card_present'] = True
                    self.state['card_uid'] = card['uid_hex']
                    self.state['cards_scanned'] += 1
                    card_removed_time = None  # Reset timera
                    
                    self.led.blink(times=1, delay_ms=50)
                    
                    print(f"[NFC] Card detected: {card['uid_hex']}")
                    
                    # Autentykacja (tylko w trybie card_reader)
                    if self.state['current_mode'] == 'card_reader' and not self.auth.is_authenticated():
                        success = self.auth.authenticate_rfid(
                            card['uid_hex'],
                            self.config.CHIP_SECRET
                        )
                        if success:
                            print("[NFC] Authentication successful!")
                
                elif card and not card['is_new']:
                    # Ta sama karta nadal obecna
                    self.state['card_present'] = True
                    card_removed_time = None
                else:
                    # Brak karty
                    self.state['card_present'] = False
                    
                    if self.state['current_mode'] == 'card_identifier':
                        # W trybie card_identifier - trzymaj UID przez 3 sekundy
                        if self.state['card_uid'] is not None:
                            if card_removed_time is None:
                                card_removed_time = time.time()
                            elif time.time() - card_removed_time >= 3:
                                # Minęły 3 sekundy - wyczyść UID
                                self.state['card_uid'] = None
                                card_removed_time = None
                    else:
                        # W innych trybach - natychmiast wyczyść
                        self.state['card_uid'] = None
            else:
                # Poza trybami skanowania - reset
                card_removed_time = None
            
            await asyncio.sleep(0.2)  # Scan co 200ms
    
    async def wifi_keep_alive_task(self):
        """Task: WiFi keep-alive (async)"""
        print("[Task] WiFi keep-alive task started")
        
        while True:
            if self.state['wifi_connected']:
                # Sprawdź połączenie
                if not self.network.is_connected():
                    print("[WiFi] Connection lost!")
                    self.state['wifi_connected'] = False
            
            await asyncio.sleep(5)  # Sprawdzaj co 5s
    
    async def input_handler_task(self):
        """Task: Obsługa wejść (encoder, button)"""
        print("[Task] Input handler task started")
        
        while True:
            # Update button state
            self.button.update()
            
            # Sprawdź encoder
            if self.encoder.has_changed():
                current_val = self.encoder.read()
                
                if self.state['current_mode'] == 'home':
                    # W menu głównym - nawigacja
                    self.menu.current_index = current_val
                    print(f"[Input] Menu index: {current_val}")
            
            # Sprawdź button
            if self.button.is_pressed():
                print("[Input] Button pressed")
                
                if self.state['current_mode'] == 'home':
                    # Enter submenu
                    selected = self.menu.get_selected_item()
                    
                    if selected == 'Card Reader':
                        self.state['current_mode'] = 'card_reader'
                        self.renderer.set_view(self.views['card_reader'])
                    elif selected == 'Card Identifier':
                        self.state['current_mode'] = 'card_identifier'
                        self.state['card_uid'] = None  # Reset UID
                        self.renderer.set_view(self.views['card_identifier'])
                    elif selected == 'WiFi':
                        self.state['current_mode'] = 'wifi'
                        self.renderer.set_view(self.views['wifi'])
                    elif selected == 'Settings':
                        self.state['current_mode'] = 'settings'
                        self.renderer.set_view(self.views['settings'])
                    
                    self.menu.enter_submenu()
            
            if self.button.was_long_press():
                # Long press - wróć do home
                print("[Input] Long press - back to home")
                self.state['current_mode'] = 'home'
                self.renderer.set_view(self.views['home'])
                self.menu.exit_submenu()
            
            await asyncio.sleep_ms(10)  # Poll co 10ms
    
    async def render_task(self):
        """Task: Renderowanie UI"""
        print("[Task] Render task started")
        
        while True:
            # Przygotuj dane dla widoku
            view_data = {
                'menu_items': self.menu.menu_items,
                'selected_index': self.menu.get_selected_index(),
                'card_present': self.state['card_present'],
                'card_uid': self.state['card_uid'],
                'cards_scanned': self.state['cards_scanned'],
                'connected': self.state['wifi_connected'],
                'ssid': self.network.get_status()['ssid'],
                'ip': self.network.get_status()['ip'],
            }
            
            # Update renderer data
            self.renderer.update_data(view_data)
            
            # Render
            self.renderer.render()
            
            await asyncio.sleep_ms(100)  # Render co 100ms (10 FPS)
    
    async def storage_auto_save_task(self):
        """Task: Automatyczny zapis storage"""
        print("[Task] Storage auto-save task started")
        
        while True:
            await asyncio.sleep(30)  # Co 30s
            
            if self.storage.has_changes():
                print("[Storage] Auto-saving...")
                self.storage.save()
    
    async def run(self):
        """Uruchom aplikację (main async loop)"""
        print("[App] Starting async tasks...")
        
        # Dodaj wszystkie zadania
        self.tasks.add_task(self.nfc_scan_task(), "NFC Scanner")
        self.tasks.add_task(self.wifi_keep_alive_task(), "WiFi Keep-Alive")
        self.tasks.add_task(self.input_handler_task(), "Input Handler")
        self.tasks.add_task(self.render_task(), "Renderer")
        self.tasks.add_task(self.storage_auto_save_task(), "Storage Auto-Save")
        
        # Uruchom wszystkie zadania
        try:
            await self.tasks.run_all()
        except KeyboardInterrupt:
            print("\n[App] Shutting down...")
            self.storage.save()
            self.display.clear()
            self.display.text("Goodbye!", 35, 28)
            self.display.show()


# ===== PUNKT WEJŚCIA =====

def main():
    """Main entry point"""
    # Załaduj konfigurację
    config = Config()
    
    # Utwórz aplikację
    app = App(config)
    
    # Setup
    app.setup()
    
    # Uruchom asyncio event loop
    try:
        asyncio.run(app.run())
    except Exception as e:
        print(f"\n[Main] Critical error: {e}")
        import sys
        sys.print_exception(e)


if __name__ == '__main__':
    main()
