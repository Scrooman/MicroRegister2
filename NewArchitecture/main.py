"""
Main Application - ESP32 
Centralna klasa App z Dependency Injection
"""

import uasyncio as asyncio # type: ignore
from machine import Pin # type: ignore

import time
from config import Config

# Warstwa 1: Drivers
from drivers.encoder import Encoder
from drivers.button import Button
from drivers.dual_led import DualLED 
from drivers.display_driver import Display
from drivers.nfc_reader import NFCReader
from drivers.nfc_reader import NFCReader
from drivers.keypad import Keypad
from drivers.wake_button import WakeButton  # ZMIANA: zamiast TouchSensor

# Warstwa 2: Services
from services.storage_manager import StorageManager
from services.network_manager import NetworkManager
from services.auth_manager import AuthManager
from services.task_manager import TaskManager
from services.sleep_manager import SleepManager

# Warstwa 3: UI
from ui.views import HomeView, CardReaderView, WiFiView, SettingsView, CardIdentifierView, KeypadView
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
        self.keypad = None
        self.wake_button = None  # ZMIANA: zamiast touch_sensor
        
        # Warstwa 2: Services
        self.storage = StorageManager()
        self.network = NetworkManager(config.SERVER_URL)
        self.auth = AuthManager(self.storage, self.network)
        self.tasks = TaskManager()
        self.sleep = None
        
        # Warstwa 3: UI
        self.renderer = None
        self.menu = None
        self.views = {}
        
        # Stan aplikacji (shared state)
        self.state = {
            'current_mode': 'home',  # home, card_reader, card_identifier, wifi, settings, keypad
            'card_present': False,
            'card_uid': None,
            'cards_scanned': 0,
            'wifi_connected': False,
            'last_update': 0,
            'keypad_buffer': '',
            'keypad_max_length': 4,
            'pending_card_uid': None,  # UID karty oczekującej na kod PIN
            'popup_message': [],
            'popup_until': 0,

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
        # wyświelt diodę, jesli połączono z WiFi
        if self.state['wifi_connected']:
            self.led.show_mode('positive_confirmation')  # Zielone mrugnięcie dla sukcesu
        else:
            self.led.show_mode('negative_error')  # Czerwone mrugnięcie dla błędu

        
    
    def _setup_hardware(self):
        """Setup hardware drivers"""
        cfg = self.config
        
        # Dual LED (ZMIANA: zamiast zwykłego LED)
        self.led = DualLED(cfg.LED_POSITIVE_PIN, cfg.LED_NEGATIVE_PIN)
        self.led.show_mode('alternating')  # Test na starcie
        
        
        # Display
        self.display = Display(cfg.OLED_SCL, cfg.OLED_SDA)
        self.display.text("Initializing...", 10, 25)
        self.display.show()
        
        # Encoder
        self.encoder = Encoder(
            cfg.ENC_CLK,
            cfg.ENC_DT,
            min_val=0,
            max_val=4,  # 5 menu items (Card Reader, Card Identifier, WiFi, Keypad, Settings)
            wrap=True
        )
        
        # Button
        self.button = Button(cfg.ENC_SW)
        
        # NFC Reader
        self.nfc_reader = NFCReader(cfg.NFC_SCL, cfg.NFC_SDA)

        # Keypad
        self.keypad = Keypad(
            cfg.KEYPAD_ROW_PINS,
            cfg.KEYPAD_COL_PINS,
            cfg.KEYPAD_VALUES,
            cfg.KEYPAD_MAX_LENGTH
        )

        # Wake Button (ZMIANA: zamiast TouchSensor)
        self.wake_button = WakeButton(
            cfg.WAKE_BUTTON_PIN,
            pull_up=cfg.WAKE_BUTTON_PULL_UP,
            debounce_ms=cfg.WAKE_BUTTON_DEBOUNCE_MS
        )
        
        # Sleep Manager
        self.sleep = SleepManager(
            self.wake_button,  # ZMIANA: wake_button zamiast touch_sensor
            self.display,
            cfg.SLEEP_INACTIVITY_TIMEOUT
        )
        self.sleep.enable_sleep(cfg.SLEEP_ENABLED)
    
    
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
            #'settings': SettingsView(),
            'keypad': KeypadView()
        }
        
        # Menu Manager
        self.menu = MenuManager(self.renderer)
        self.menu.set_menu_items(['Card Reader', 'Card Identifier', 'WiFi', 'Keypad', 'Settings'])
        
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
                    
                    await self.led.show_mode_async('positive_quick')  # Szybkie zielone mrugnięcie dla nowej karty

                    
                    print(f"[NFC] Card detected: {card['uid_hex']}")
                    if self.state['current_mode'] == 'card_reader':
                    
                        # # Autentykacja (tylko w trybie card_reader)
                        # if self.state['current_mode'] == 'card_reader' and not self.auth.is_authenticated():
                        #     success = self.auth.authenticate_rfid(
                        #         card['uid_hex'],
                        #         self.config.CHIP_SECRET
                        #     )
                        #     if success:
                        #         print("[NFC] Authentication successful!")

                        # wyślij żądanie do serwera o wykryciu karty
                        # wyświetl informację o przetwarzaniu odczytanej karty
                        self.display.clear()
                        self.display.text("Card detected", 10, 25)
                        self.display.text("Processing...", 10, 40)
                        self.display.show()
                        send_chip_detection_response = self.auth.send_chip_detection(card['uid_hex'])
                        if not send_chip_detection_response['success']:
                            await self.led.show_mode_async('negative_error')  # Czerwone mrugnięcie dla błędu

                            print("[NFC] Failed to send chip detection to server!")
                            if send_chip_detection_response['error'] == 401:
                                print("[NFC] Authentication error when sending chip detection!")
                                self.state['popup_message'] = [
                                    "Authentication error!",
                                    "Please authenticate again."
                                ]
                                self.state['popup_until'] = time.time() + 5  # Wyświetl przez 5 sekund
                            else:

                                self.state['popup_message'] = [
                                    "Undefined chip"
                                ]
                                self.state['popup_until'] = time.time() + 5  # Wyświetl przez 5 sekund

                        else:
                            print("[NFC] Chip detection sent to server successfully!")
                            chip_detection_data = send_chip_detection_response.get('result', {})
                            # zapisz dane o wykryciu karty do stanu aplikacji
                            self.state['scanned_chips_task_name'] = chip_detection_data.get('task_name', 'Unknown Task')
                            self.state['scanned_chips_task_start_time'] = chip_detection_data.get('task_start_time', 'Unknown Time')
                            # self.state['popup_message'] = [
                            #     "Task detected:",
                            #     chip_detection_data.get('task_name', 'Unknown Task'),
                            #     chip_detection_data.get('task_start_time', 'Unknown Time')
                            # ]
                            # self.state['popup_until'] = time.time() + 5  # Wyświetl przez 5 sekund

                
                elif card and not card['is_new']:
                    # Ta sama karta nadal obecna
                    self.state['card_present'] = True
                    card_removed_time = None
                else:
                    # Brak karty
                    self.state['card_present'] = False
                    
                    # W card_identifier - nie czyść UID od razu (czekaj na przycisk)
                    # W innych trybach - wyczyść natychmiast
                    if self.state['current_mode'] != 'card_identifier':
                        self.state['card_uid'] = None
            else:
                # Poza trybami skanowania - reset
                card_removed_time = None
            
            await asyncio.sleep(2)  # Scan co 2s
    
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
            # reset timera przy jakiejkolwiek aktywności
           
            
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
                    elif selected == 'Keypad':
                        self.state['current_mode'] = 'keypad'
                        self.keypad.clear_buffer()
                        self.state['keypad_buffer'] = ''
                        self.renderer.set_view(self.views['keypad'])
                    elif selected == 'Settings':
                        self.state['current_mode'] = 'settings'
                        self.renderer.set_view(self.views['settings'])
                    
                    self.menu.enter_submenu()

                elif self.state['current_mode'] == 'card_identifier':
                    # W trybie card_identifier - po odczytaniu karty przejdź do keypad
                    if self.state['card_uid'] is not None:
                        print(f"[CardIdentifier] Card UID: {self.state['card_uid']}")
                        print("[CardIdentifier] Switching to keypad for PIN entry...")
                        
                        # Zapisz UID karty do późniejszego użycia
                        self.state['pending_card_uid'] = self.state['card_uid']
                        
                        # Przejdź do trybu keypad
                        self.state['current_mode'] = 'keypad'
                        self.keypad.clear_buffer()
                        self.state['keypad_buffer'] = ''
                        self.renderer.set_view(self.views['keypad'])

                elif self.state['current_mode'] == 'keypad':
                    # W trybie keypad - potwierdź kod
                    if self.keypad.is_buffer_full():
                        code = self.keypad.get_buffer()
                        print(f"[Keypad] Code entered: {code}")
                        
                        # Wywołaj funkcję weryfikacji
                        await self.process_card_and_pin(self.state['pending_card_uid'], code)
                        
                        # Wróć do card_identifier lub home
                        await self.led.show_mode_async('positive_success')  # Zielone mrugnięcie dla sukcesu

                        
                        # Reset stanu
                        self.state['pending_card_uid'] = None
                        self.keypad.clear_buffer()
                        self.state['keypad_buffer'] = ''
                        
                        # Wróć do home
                        self.state['current_mode'] = 'home'
                        self.state['card_uid'] = None
                        self.renderer.set_view(self.views['home'])
                        self.menu.exit_submenu()
            
            if self.button.was_long_press():
                # Long press - wróć do home
                print("[Input] Long press - back to home")
                self.state['current_mode'] = 'home'
                self.state['card_uid'] = None  # Wyczyść UID przy powrocie
                self.renderer.set_view(self.views['home'])
                self.menu.exit_submenu()
            
            await asyncio.sleep_ms(10)  # Poll co 10ms


    async def process_card_and_pin(self, card_uid, pin_code):
        """
        Przetwórz UID karty i kod PIN (zmockowana funkcja)
        
        Args:
            card_uid: UID odczytanej karty
            pin_code: Wprowadzony kod PIN
        """
        print("\n" + "="*50)
        print("Processing card and PIN...")
        print(f"  Card UID: {card_uid}")
        print(f"  PIN Code: {pin_code}")
        print("="*50 + "\n")

        authenticate_chip_response = self.auth.authenticate_rfid(card_uid, pin_code)
        if not authenticate_chip_response["success"]:
            print("Authentication failed!")
            # wyŚwietl komunikat o błędzie na ekranie
            self.display.clear()
            self.display.text("Authentication Failed!", 10, 25)
            self.display.show()
            await self.led.show_mode_async('negative_error')  # Czerwone mrugnięcie dla błędu
            return False
        else:
            print("Authentication successful!")
            await self.led.show_mode_async('positive_success')  # Zielone mrugnięcie dla sukcesu
            # wyświetl komunikat o sukcesie na ekranie
            self.display.clear()
            self.display.text("Access Granted!", 10, 25)
            self.display.show()
            return True
        
        # Symulacja opóźnienia przetwarzania
        #await asyncio.sleep(1)
        
    
    # DODAJ nowy task
    async def sleep_monitor_task(self):
        """Task: Monitorowanie uśpienia i wybudzania"""
        print("[Task] Sleep monitor task started")
        
        while True:
            # Sprawdź warunek wybudzenia (dotyk)
            if self.sleep.check_wake_condition():
                # Urządzenie zostało obudzone - odśwież ekran
                pass
            
            # Sprawdź czas bezczynności
            if not self.sleep.is_sleeping:
                self.sleep.check_inactivity()
            
            await asyncio.sleep_ms(100)  # Sprawdzaj co 100ms
    

    
    async def render_task(self):
        """Task: Renderowanie UI"""
        print("[Task] Render task started")
        
        while True:

            # DODAJ - nie renderuj jeśli urządzenie śpi
            if self.sleep.is_sleeping:
                await asyncio.sleep_ms(500)
                continue

            # Przygotuj dane dla widoku
            view_data = {
                'menu_items': self.menu.menu_items,
                'selected_index': self.menu.get_selected_index(),
                'card_present': self.state['card_present'],
                'card_uid': self.state['card_uid'],
                'scanned_chips_task_name': self.state.get('scanned_chips_task_name', 'Unknown'),
                'scanned_chips_task_start_time': self.state.get('scanned_chips_task_start_time', 'Unknown'),
                'cards_scanned': self.state['cards_scanned'],
                'connected': self.state['wifi_connected'],
                'ssid': self.network.get_status()['ssid'],
                'ip': self.network.get_status()['ip'],
                'keypad_buffer': self.state['keypad_buffer'],
                'keypad_max_length': self.state['keypad_max_length'],
                'pending_card_uid': self.state['pending_card_uid'],

            }
            
            # Update renderer data
            self.renderer.update_data(view_data)
            
            # Render
            self.renderer.render()

            # Obsługa popup
            if self.state.get('popup_message') and time.time() < self.state.get('popup_until', 0):
                self.display.clear()
                for idx, line in enumerate(self.state['popup_message']):
                    self.display.text(line, 10, 25 + idx * 15)
                self.display.show()
            else:
                self.state['popup_message'] = []
                self.renderer.update_data(view_data)
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

    async def keypad_input_task(self):
        """Task: Obsługa klawiatury"""
        print("[Task] Keypad input task started")
        
        while True:
            if self.state['current_mode'] == 'keypad':
                # Odczytaj klawisz
                key = self.keypad.read()
                
                if key is not None:

                    # Dodaj do bufora
                    if self.keypad.add_to_buffer(key):
                        self.state['keypad_buffer'] = self.keypad.get_buffer()
                        await self.led.show_mode_async('positive_quick')  # Szybkie zielone mrugnięcie dla nowej karty
                        print(f"[Keypad] Key pressed: {key}, Buffer: {self.state['keypad_buffer']}")
            
            await asyncio.sleep_ms(50)  # Poll co 50ms
    
    async def run(self):
        """Uruchom aplikację (main async loop)"""
        print("[App] Starting async tasks...")
        
        # Dodaj wszystkie zadania
        self.tasks.add_task(self.nfc_scan_task(), "NFC Scanner")
        self.tasks.add_task(self.wifi_keep_alive_task(), "WiFi Keep-Alive")
        self.tasks.add_task(self.input_handler_task(), "Input Handler")
        self.tasks.add_task(self.keypad_input_task(), "Keypad Input")
        self.tasks.add_task(self.render_task(), "Renderer")
        self.tasks.add_task(self.storage_auto_save_task(), "Storage Auto-Save")
        self.tasks.add_task(self.sleep_monitor_task(), "Sleep Monitor")
        
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
