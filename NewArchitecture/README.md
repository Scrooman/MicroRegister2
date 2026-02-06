# ESP32 MicroPython - Architektura 3-Warstwowa

Aplikacja ESP32 oparta na MicroPython z czystą architekturą 3-warstwową, asynchronicznym programowaniem (asyncio) i Dependency Injection.

## 📋 Struktura Projektu

```
NewArchitecture/
│
├── boot.py                    # Boot loader
├── main.py                    # Punkt wejścia aplikacji
├── config.py                  # Konfiguracja
│
├── drivers/                   # WARSTWA 1: Hardware Drivers
│   ├── __init__.py
│   ├── encoder.py             # Rotary encoder driver
│   ├── button.py              # Button driver (debouncing)
│   ├── led.py                 # LED driver
│   ├── display_driver.py      # OLED SSD1306 driver
│   └── nfc_reader.py          # NFC PN532 reader
│
├── services/                  # WARSTWA 2: Business Logic
│   ├── __init__.py
│   ├── storage_manager.py     # JSON persistence
│   ├── network_manager.py     # WiFi + HTTP client
│   ├── auth_manager.py        # Authentication
│   └── task_manager.py        # Asyncio task coordinator
│
├── ui/                        # WARSTWA 3: UI Engine
│   ├── __init__.py
│   ├── views.py               # Screen definitions
│   ├── menu_manager.py        # Menu controller
│   └── renderer.py            # Rendering engine
│
├── lib/                       # Biblioteki zewnętrzne
│   ├── ssd1306.py
│   ├── pn532.py
│   ├── pn532_i2c.py
│   ├── rotary.py
│   └── rotary_irq_esp.py
│
└── utils/                     # Narzędzia pomocnicze
    └── __init__.py
```

## 🏗️ Architektura

### Warstwa 1: Hardware Drivers
- **Cel**: Abstrakcja sprzętu
- **Odpowiedzialność**: Ukrycie szczegółów I2C/SPI, proste API dla hardware
- **Przykład**: `encoder.read()`, `nfc_reader.read_card()`

### Warstwa 2: Services
- **Cel**: Logika biznesowa
- **Odpowiedzialność**: Zarządzanie danymi, komunikacja sieciowa, autentykacja
- **Przykład**: `storage.set()`, `network.http_post()`, `auth.authenticate_rfid()`

### Warstwa 3: UI Engine
- **Cel**: Interfejs użytkownika
- **Odpowiedzialność**: Renderowanie widoków, obsługa menu, nawigacja
- **Przykład**: `renderer.render()`, `menu.navigate_next()`

## 🚀 Uruchomienie

### 1. Flash MicroPython firmware
```bash
esptool.py --chip esp32 --port COM3 erase_flash
esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 esp32-firmware.bin
```

### 2. Konfiguracja WiFi
Edytuj `config.py`:
```python
WIFI_SSID = "TwojaSiec"
WIFI_PASSWORD = "TwojeHaslo"
SERVER_URL = "http://192.168.0.16:5000"
```

### 3. Upload plików
```bash
# Użyj Pymakr lub mpremote
mpremote connect COM3 fs cp -r . :
```

### 4. Uruchom
```bash
mpremote connect COM3 run main.py
```

## 🔧 Konfiguracja Hardware

### Piny GPIO
- **LED**: Pin 2
- **Encoder CLK**: Pin 4
- **Encoder DT**: Pin 16
- **Encoder SW (Button)**: Pin 17
- **OLED SCL**: Pin 22
- **OLED SDA**: Pin 21
- **NFC SCL**: Pin 18
- **NFC SDA**: Pin 19

### Komponenty
- ESP32 DevKit
- OLED Display 128x64 (SSD1306, I2C)
- NFC Reader PN532 (I2C)
- Rotary Encoder z przyciskiem
- LED

## 💡 Użycie

### Menu Główne
- Obracaj enkoderem aby nawigować
- Naciśnij przycisk aby wejść do menu
- Długie naciśnięcie aby wrócić do głównego menu

### Tryby
1. **Card Reader** - Skanowanie kart NFC/RFID
2. **WiFi** - Status połączenia WiFi
3. **Settings** - Ustawienia aplikacji
4. **About** - Informacje o aplikacji

## 📚 API

### Drivers API
```python
# Encoder
encoder = Encoder(clk_pin=4, dt_pin=16, min_val=0, max_val=10)
value = encoder.read()
changed = encoder.has_changed()

# Button
button = Button(pin_num=17)
button.update()  # Wywołuj w każdej iteracji!
if button.is_pressed():
    print("Pressed!")

# Display
display = Display(scl_pin=22, sda_pin=21)
display.clear()
display.text("Hello", 0, 0)
display.show()

# NFC Reader
nfc = NFCReader(scl_pin=18, sda_pin=19)
card = nfc.read_card(timeout=0.5)
if card:
    print(card['uid_hex'])
```

### Services API
```python
# Storage Manager
storage = StorageManager('data.json')
storage.set('key', 'value')
value = storage.get('key')
storage.save()

# Network Manager
network = NetworkManager(server_url="http://192.168.0.1:5000")
network.connect_wifi("SSID", "password")
success, data = network.http_post('/api/endpoint', {'key': 'value'})

# Auth Manager
auth = AuthManager(storage, network)
auth.authenticate_rfid(rfid_uid, chip_secret)
if auth.is_authenticated():
    token = auth.get_access_token()
```

## 🎯 Kluczowe Cechy

✅ **3-warstwowa architektura** - Czysta separacja odpowiedzialności  
✅ **Dependency Injection** - App przekazuje zależności  
✅ **Asyncio** - Wszystkie zadania jako async tasks  
✅ **Shared State** - Komunikacja przez `app.state`  
✅ **Prostota** - Brak niepotrzebnych abstrakcji  
✅ **Testowalne** - Każda warstwa testowalna osobno  
✅ **Skalowalne** - Łatwe dodawanie nowych funkcji  

## 🔄 Async Tasks

Aplikacja wykorzystuje 5 równoległych zadań asynchronicznych:

1. **NFC Scanner** - Skanowanie kart NFC (200ms)
2. **WiFi Keep-Alive** - Monitorowanie połączenia WiFi (5s)
3. **Input Handler** - Obsługa enkodera i przycisku (10ms)
4. **Renderer** - Renderowanie UI (100ms, 10 FPS)
5. **Storage Auto-Save** - Automatyczny zapis danych (30s)

## 📖 Dokumentacja

Pełna dokumentacja znajduje się w pliku `AI_PROJECT_ARCHITECTURE_V2.md`

## 🐛 Debug

Aby włączyć tryb debug:
```python
# W drivers/nfc_reader.py
self.pn532 = PN532_I2C(i2c, debug=True)
```

## 📝 Licencja

MIT License

## 👤 Autor

ESP32 MicroPython Application - 2026
