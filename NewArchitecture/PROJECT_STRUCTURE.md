# Struktura Projektu ESP32 - Nowa Architektura

## 📁 Struktura Plików

```
NewArchitecture/
│
├── 📄 boot.py                           # Boot loader - inicjalizacja systemu
├── 📄 main.py                           # Punkt wejścia aplikacji (klasa App)
├── 📄 config.py                         # Konfiguracja (WiFi, piny, URL serwera)
├── 📄 README.md                         # Dokumentacja projektu
├── 📄 platformio.ini                    # Konfiguracja PlatformIO
├── 📄 pymakr.conf                       # Konfiguracja Pymakr
├── 📄 AI_PROJECT_ARCHITECTURE_V2.md     # Pełna dokumentacja architektury
│
├── 📁 drivers/                          # WARSTWA 1: Hardware Drivers
│   ├── __init__.py
│   ├── encoder.py                       # Rotary encoder driver
│   ├── button.py                        # Button driver (debouncing + long press)
│   ├── led.py                           # LED driver
│   ├── display_driver.py                # OLED SSD1306 driver (128x64)
│   └── nfc_reader.py                    # NFC PN532 reader
│
├── 📁 services/                         # WARSTWA 2: Business Logic
│   ├── __init__.py
│   ├── storage_manager.py               # JSON persistence (storage.json)
│   ├── network_manager.py               # WiFi + HTTP client
│   ├── auth_manager.py                  # Authentication (RFID, tokens)
│   └── task_manager.py                  # Asyncio task coordinator
│
├── 📁 ui/                               # WARSTWA 3: UI Engine
│   ├── __init__.py
│   ├── views.py                         # Screen definitions (Home, CardReader, WiFi, Settings)
│   ├── menu_manager.py                  # Menu controller + navigation
│   └── renderer.py                      # Rendering engine
│
├── 📁 lib/                              # Biblioteki zewnętrzne
│   ├── ssd1306.py                       # OLED driver library
│   ├── pn532.py                         # NFC base library
│   ├── pn532_i2c.py                     # NFC I2C interface
│   ├── rotary.py                        # Rotary encoder base
│   └── rotary_irq_esp.py                # Rotary encoder dla ESP32
│
└── 📁 utils/                            # Narzędzia pomocnicze
    └── __init__.py
```

## 🏗️ Architektura 3-Warstwowa

### Warstwa 1: Hardware Drivers (Abstrakcja Sprzętu)
**Odpowiedzialność:** Ukrycie szczegółów komunikacji I2C/SPI, proste API

| Plik | Komponent | Główne Metody |
|------|-----------|---------------|
| `encoder.py` | Rotary Encoder | `read()`, `has_changed()`, `get_delta()` |
| `button.py` | Przycisk | `update()`, `is_pressed()`, `was_long_press()` |
| `led.py` | LED | `on()`, `off()`, `blink()` |
| `display_driver.py` | OLED Display | `text()`, `clear()`, `show()` |
| `nfc_reader.py` | NFC Reader | `read_card()`, `is_card_present()` |

### Warstwa 2: Services (Logika Biznesowa)
**Odpowiedzialność:** Zarządzanie danymi, komunikacja sieciowa, autentykacja

| Plik | Serwis | Główne Metody |
|------|--------|---------------|
| `storage_manager.py` | Przechowywanie | `set()`, `get()`, `save()`, `get_all()` |
| `network_manager.py` | Sieć WiFi/HTTP | `connect_wifi()`, `http_post()`, `http_get()` |
| `auth_manager.py` | Autentykacja | `authenticate_rfid()`, `is_authenticated()` |
| `task_manager.py` | Zadania async | `add_task()`, `run_all()` |

### Warstwa 3: UI Engine (Interfejs Użytkownika)
**Odpowiedzialność:** Renderowanie widoków, nawigacja, obsługa menu

| Plik | Komponent | Główne Metody |
|------|-----------|---------------|
| `views.py` | Ekrany | `HomeView`, `CardReaderView`, `WiFiView`, `SettingsView` |
| `menu_manager.py` | Menu | `navigate_next()`, `get_selected_item()` |
| `renderer.py` | Renderer | `set_view()`, `render()`, `update_data()` |

## 🔄 Flow Komunikacji

### Przykład: Skanowanie Karty NFC

```
1. nfc_scan_task() (asyncio)
   ↓
2. nfc_reader.read_card()  [Warstwa 1]
   ↓
3. app.state['card_uid'] = card['uid_hex']  [Shared State]
   ↓
4. auth.authenticate_rfid()  [Warstwa 2]
   ↓
5. storage.set('rfid_uid', uid)  [Warstwa 2]
   ↓
6. render_task() odczytuje app.state  [Warstwa 3]
   ↓
7. renderer.render() → CardReaderView.render()  [Warstwa 3]
```

## 🎯 Dependency Injection

Wszystkie zależności są wstrzykiwane przez klasę `App`:

```python
# W main.py
class App:
    def __init__(self, config):
        # Warstwa 2: Services
        self.storage = StorageManager()
        self.network = NetworkManager(config.SERVER_URL)
        self.auth = AuthManager(self.storage, self.network)  # DI!
        
        # Warstwa 3: UI
        self.renderer = Renderer(self.display)  # DI!
        self.menu = MenuManager(self.renderer)  # DI!
```

## ⚙️ Zadania Asynchroniczne

Aplikacja działa w trybie asynchronicznym z 5 równoległymi zadaniami:

| Task | Częstotliwość | Odpowiedzialność |
|------|---------------|------------------|
| `nfc_scan_task()` | 200ms | Skanowanie kart NFC |
| `wifi_keep_alive_task()` | 5s | Monitorowanie WiFi |
| `input_handler_task()` | 10ms | Obsługa enkodera i przycisku |
| `render_task()` | 100ms (10 FPS) | Renderowanie UI |
| `storage_auto_save_task()` | 30s | Automatyczny zapis |

## 🔌 Konfiguracja Hardware

### Piny GPIO (config.py)
```python
LED_PIN = 2          # LED
ENC_CLK = 4          # Encoder CLK
ENC_DT = 16          # Encoder DT
ENC_SW = 17          # Encoder Button
OLED_SCL = 22        # OLED I2C SCL
OLED_SDA = 21        # OLED I2C SDA
NFC_SCL = 18         # NFC I2C SCL
NFC_SDA = 19         # NFC I2C SDA
```

## 📦 Komponenty Użyte

| Komponent | Model | Interfejs |
|-----------|-------|-----------|
| Mikrokontroler | ESP32 DevKit | - |
| Wyświetlacz | OLED 128x64 SSD1306 | I2C (0x3C) |
| Czytnik NFC | PN532 | I2C (0x24) |
| Enkoder | Rotary Encoder | GPIO + Interrupts |
| LED | Standard LED | GPIO |

## 🚀 Uruchomienie

### 1. Konfiguracja
Edytuj `config.py`:
```python
WIFI_SSID = "TwojaSiec"
WIFI_PASSWORD = "TwojeHaslo"
SERVER_URL = "http://192.168.0.16:5000"
```

### 2. Upload na ESP32
```bash
# Opcja 1: Pymakr (VSCode)
# - Otwórz projekt w VSCode
# - Podłącz ESP32
# - Użyj "Upload Project"

# Opcja 2: mpremote
mpremote connect COM3 fs cp -r . :
mpremote connect COM3 run main.py
```

## 🎮 Użytkowanie

### Nawigacja
- **Obrót enkodera**: Nawigacja w menu
- **Krótkie naciśnięcie**: Wejście do menu / Akcja
- **Długie naciśnięcie**: Powrót do menu głównego

### Menu
1. **Card Reader** - Tryb skanowania kart NFC/RFID
2. **WiFi** - Status i zarządzanie WiFi
3. **Settings** - Ustawienia
4. **About** - Informacje

## 📊 Statystyki

- **Plików kodu**: 17
- **Warstw architektonicznych**: 3
- **Zadań asynchronicznych**: 5
- **Komponentów hardware**: 5
- **Ekranów UI**: 4

## 🔧 Rozwój

### Dodawanie nowego drivera (Warstwa 1)
```python
# drivers/new_sensor.py
class NewSensor:
    def __init__(self, pin):
        self._pin = Pin(pin)
    
    def read(self):
        return self._pin.value()
```

### Dodawanie nowego serwisu (Warstwa 2)
```python
# services/new_service.py
class NewService:
    def __init__(self, storage, network):
        self.storage = storage
        self.network = network
    
    def do_something(self):
        pass
```

### Dodawanie nowego widoku (Warstwa 3)
```python
# W ui/views.py
class NewView(View):
    def __init__(self):
        super().__init__("NewView")
    
    def render(self, display, data):
        display.clear()
        display.text("New View", 30, 0)
        display.show()
```

## 📝 Kluczowe Zasady

✅ **Warstwa nie zna warstwy wyżej** - Drivers nie wiedzą o Services ani UI  
✅ **Dependency Injection przez App** - Wszystkie zależności przez konstruktor  
✅ **Shared State** - Komunikacja między zadaniami przez `app.state`  
✅ **Async/Await** - Wszystkie długie operacje asynchroniczne  
✅ **Prostota** - Bez nadmiernych abstrakcji  

## 🎯 Cele Projektu

- [x] Czysta architektura 3-warstwowa
- [x] Dependency Injection
- [x] Programowanie asynchroniczne (asyncio)
- [x] Obsługa NFC/RFID
- [x] WiFi + HTTP client
- [x] UI z menu i nawigacją
- [x] Persystencja danych (JSON)
- [x] Autentykacja RFID

---

**Projekt gotowy do uruchomienia!** 🚀
