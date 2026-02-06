# Instrukcje AI: Architektura 3-Warstwowa ESP32 MicroPython

## 📋 Cel
Stwórz nowy projekt ESP32 z MicroPython oparty na **3-warstwowej architekturze** bez Event Bus, wykorzystując istniejące komponenty jako bazę, z implementacją programowania asynchronicznego i bezpośrednim przekazywaniem zależności (Dependency Injection).

---

## 🏗️ Architektura 3-Warstwowa (Uproszczona)

```
┌─────────────────────────────────────────────────────────────┐
│  Warstwa 3: View & Controller (UI Engine)                   │
│  ─────────────────────────────────────────────────────────  │
│  • menu_manager.py       - Kontroler menu i nawigacji       │
│  • views.py              - Definicje ekranów/widoków        │
│  • renderer.py           - Renderowanie na OLED             │
│  ─────────────────────────────────────────────────────────  │
│  Zasada: Kontroler pobiera dane z Warstwy 1 i używa        │
│          Warstwy 2 do operacji. Aktualizuje UI.             │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│  Warstwa 2: Services (Business Logic)                       │
│  ─────────────────────────────────────────────────────────  │
│  • network_manager.py    - WiFi + HTTP                      │
│  • storage_manager.py    - JSON persistence                 │
│  • auth_manager.py       - Autentykacja (RFID, tokeny)      │
│  • task_manager.py       - Koordynacja zadań asyncio        │
│  ─────────────────────────────────────────────────────────  │
│  Zasada: Logika biznesowa. Decyduje co zrobić z danymi.    │
│          Nie zna szczegółów hardware.                       │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│  Warstwa 1: Hardware Abstraction (Drivers)                  │
│  ─────────────────────────────────────────────────────────  │
│  • encoder.py            - Rotary encoder driver            │
│  • button.py             - Button driver (debouncing)       │
│  • led.py                - LED driver                       │
│  • display_driver.py     - OLED SSD1306 driver              │
│  • nfc_reader.py         - NFC PN532 reader                 │
│  ─────────────────────────────────────────────────────────  │
│  Zasada: Opakowania podzespołów. Ukrycie I2C/SPI.          │
│          Proste API: "ile kliknięć?", "jaki UID karty?".   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Struktura Repozytorium

```
esp32-app/
│
├── README.md                          # Dokumentacja projektu
├── requirements.txt                   # Zależności (dev tools)
├── platformio.ini                     # Konfiguracja PlatformIO
├── pymakr.conf                        # Konfiguracja Pymakr
│
├── boot.py                            # Boot loader (import gc, init)
├── main.py                            # Punkt wejścia - App class + asyncio
├── config.py                          # Konfiguracja (WiFi, pins, URLs)
│
├── drivers/                           # WARSTWA 1: Hardware Drivers
│   ├── __init__.py
│   ├── encoder.py                     # Rotary encoder
│   ├── button.py                      # Button z debouncing
│   ├── led.py                         # LED control
│   ├── display_driver.py              # OLED display
│   └── nfc_reader.py                  # NFC PN532 reader
│
├── services/                          # WARSTWA 2: Business Logic
│   ├── __init__.py
│   ├── network_manager.py             # WiFi + HTTP client
│   ├── storage_manager.py             # JSON storage
│   ├── auth_manager.py                # Authentication logic
│   └── task_manager.py                # Asyncio task coordinator
│
├── ui/                                # WARSTWA 3: UI Engine
│   ├── __init__.py
│   ├── menu_manager.py                # Menu controller
│   ├── views.py                       # Screen definitions
│   └── renderer.py                    # Rendering engine
│
├── lib/                               # Biblioteki zewnętrzne
│   ├── ssd1306.py                     # OLED library
│   ├── pn532.py                       # NFC library
│   ├── pn532_i2c.py                   # NFC I2C interface
│   ├── rotary.py                      # Rotary base
│   └── rotary_irq_esp.py             # Rotary for ESP32
│
├── utils/                             # Narzędzia pomocnicze
│   ├── __init__.py
│   └── logger.py                      # Logging utility
│
├── tests/                             # Testy
│   ├── test_drivers/
│   ├── test_services/
│   └── test_ui/
│
└── docs/                              # Dokumentacja
    ├── architecture.md
    ├── hardware.md
    └── api.md
```

---

## 🔧 Implementacja Warstwy 1: Hardware Drivers

### `drivers/encoder.py`
```python
"""Rotary Encoder Driver"""

from rotary_irq_esp import RotaryIRQ

class Encoder:
    """Wrapper dla enkodera obrotowego - zwraca tylko wartość"""
    
    def __init__(self, clk_pin: int, dt_pin: int, min_val=0, max_val=10, 
                 reverse=False, wrap=True):
        """
        Args:
            clk_pin: Pin CLK
            dt_pin: Pin DT
            min_val: Minimalna wartość
            max_val: Maksymalna wartość
            reverse: Odwróć kierunek
            wrap: Zapętlenie wartości
        """
        self._encoder = RotaryIRQ(
            pin_num_clk=clk_pin,
            pin_num_dt=dt_pin,
            min_val=min_val,
            max_val=max_val,
            reverse=reverse,
            range_mode=RotaryIRQ.RANGE_WRAP if wrap else RotaryIRQ.RANGE_BOUNDED
        )
        self._last_value = self._encoder.value()
    
    def read(self) -> int:
        """Odczytaj aktualną wartość enkodera"""
        return self._encoder.value()
    
    def has_changed(self) -> bool:
        """Sprawdź czy wartość się zmieniła od ostatniego odczytu"""
        current = self._encoder.value()
        changed = current != self._last_value
        if changed:
            self._last_value = current
        return changed
    
    def get_delta(self) -> int:
        """Pobierz różnicę od ostatniego odczytu"""
        current = self._encoder.value()
        delta = current - self._last_value
        self._last_value = current
        return delta
    
    def set_range(self, min_val: int, max_val: int):
        """Ustaw zakres wartości"""
        self._encoder.set(min_val=min_val, max_val=max_val)
    
    def reset(self, value: int = 0):
        """Resetuj wartość"""
        self._encoder.set(value=value)
        self._last_value = value
```

### `drivers/button.py`
```python
"""Button Driver z debouncing"""

from machine import Pin
import time

class Button:
    """Obsługa przycisku z debouncing i long press"""
    
    def __init__(self, pin_num: int, pull_up=True, debounce_ms=50, long_press_ms=1000):
        """
        Args:
            pin_num: Numer pinu
            pull_up: Użyj pull-up (True) lub pull-down (False)
            debounce_ms: Czas debouncing w ms
            long_press_ms: Czas długiego wciśnięcia w ms
        """
        pull = Pin.PULL_UP if pull_up else Pin.PULL_DOWN
        self._pin = Pin(pin_num, Pin.IN, pull)
        self._debounce_ms = debounce_ms
        self._long_press_ms = long_press_ms
        
        self._last_state = self._pin.value()
        self._last_change_time = time.ticks_ms()
        self._press_start_time = 0
        
        # Flagi stanu (resetowane po odczycie)
        self._pressed = False
        self._released = False
        self._long_press_detected = False
    
    def update(self):
        """Aktualizuj stan przycisku - WYWOŁUJ W KAŻDEJ ITERACJI"""
        current_state = self._pin.value()
        current_time = time.ticks_ms()
        
        # Reset flag
        self._pressed = False
        self._released = False
        self._long_press_detected = False
        
        # Sprawdź zmianę stanu z debouncing
        if current_state != self._last_state:
            if time.ticks_diff(current_time, self._last_change_time) > self._debounce_ms:
                # Stan się zmienił
                if current_state == 0:  # Wciśnięcie (pull-up = 0 when pressed)
                    self._pressed = True
                    self._press_start_time = current_time
                else:  # Puszczenie
                    self._released = True
                    press_duration = time.ticks_diff(current_time, self._press_start_time)
                    if press_duration >= self._long_press_ms:
                        self._long_press_detected = True
                
                self._last_state = current_state
                self._last_change_time = current_time
    
    def is_pressed(self) -> bool:
        """True jeśli przycisk został wciśnięty w tej iteracji"""
        return self._pressed
    
    def is_released(self) -> bool:
        """True jeśli przycisk został puszczony w tej iteracji"""
        return self._released
    
    def was_long_press(self) -> bool:
        """True jeśli ostatnie wciśnięcie było długie"""
        return self._long_press_detected
    
    def is_down(self) -> bool:
        """True jeśli przycisk jest aktualnie wciśnięty"""
        return self._last_state == 0
```

### `drivers/led.py`
```python
"""LED Driver"""

from machine import Pin
import time

class LED:
    """Prosty sterownik LED"""
    
    def __init__(self, pin_num: int):
        """
        Args:
            pin_num: Numer pinu GPIO
        """
        self._pin = Pin(pin_num, Pin.OUT)
        self._state = False
    
    def on(self):
        """Włącz LED"""
        self._pin.value(1)
        self._state = True
    
    def off(self):
        """Wyłącz LED"""
        self._pin.value(0)
        self._state = False
    
    def toggle(self):
        """Przełącz stan LED"""
        self._state = not self._state
        self._pin.value(1 if self._state else 0)
    
    def blink(self, times=1, delay_ms=100):
        """
        Mrugnij LED
        
        Args:
            times: Ile razy
            delay_ms: Opóźnienie między migami
        """
        for _ in range(times):
            self.on()
            time.sleep_ms(delay_ms)
            self.off()
            time.sleep_ms(delay_ms)
    
    def is_on(self) -> bool:
        """Sprawdź czy LED jest włączony"""
        return self._state
```

### `drivers/display_driver.py`
```python
"""OLED Display Driver (SSD1306)"""

from machine import Pin, SoftI2C
import ssd1306

class Display:
    """Sterownik wyświetlacza OLED 128x64"""
    
    def __init__(self, scl_pin: int, sda_pin: int, width=128, height=64):
        """
        Args:
            scl_pin: Pin SCL dla I2C
            sda_pin: Pin SDA dla I2C
            width: Szerokość w pikselach
            height: Wysokość w pikselach
        """
        i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.oled = ssd1306.SSD1306_I2C(width, height, i2c)
        self.width = width
        self.height = height
        self.clear()
    
    def clear(self):
        """Wyczyść ekran"""
        self.oled.fill(0)
    
    def show(self):
        """Wyświetl bufor na ekranie"""
        self.oled.show()
    
    def text(self, text: str, x: int, y: int):
        """
        Wyświetl tekst
        
        Args:
            text: Tekst do wyświetlenia
            x: Pozycja X (0-127)
            y: Pozycja Y (0-63)
        """
        self.oled.text(text, x, y)
    
    def pixel(self, x: int, y: int, color: int):
        """Ustaw piksel"""
        self.oled.pixel(x, y, color)
    
    def line(self, x1: int, y1: int, x2: int, y2: int, color: int):
        """Narysuj linię"""
        self.oled.line(x1, y1, x2, y2, color)
    
    def rect(self, x: int, y: int, w: int, h: int, color: int, fill=False):
        """Narysuj prostokąt"""
        if fill:
            self.oled.fill_rect(x, y, w, h, color)
        else:
            self.oled.rect(x, y, w, h, color)
    
    def contrast(self, value: int):
        """Ustaw kontrast (0-255)"""
        self.oled.contrast(value)
    
    def invert(self, invert: bool):
        """Odwróć kolory"""
        self.oled.invert(invert)
```

### `drivers/nfc_reader.py`
```python
"""NFC Reader Driver (PN532)"""

from machine import I2C, Pin
from pn532_i2c import PN532_I2C

class NFCReader:
    """Sterownik czytnika NFC PN532"""
    
    def __init__(self, scl_pin: int, sda_pin: int, i2c_id=1):
        """
        Args:
            scl_pin: Pin SCL dla I2C
            sda_pin: Pin SDA dla I2C
            i2c_id: ID magistrali I2C
        """
        self.available = False
        self._last_uid = None
        
        try:
            i2c = I2C(i2c_id, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000)
            self.pn532 = PN532_I2C(i2c, debug=False)
            
            # Sprawdź firmware
            ic, ver, rev, support = self.pn532.firmware_version
            print(f"[NFC] PN532 v{ver}.{rev} detected")
            
            # Konfiguruj czytnik
            self.pn532.SAM_configuration()
            self.available = True
            
        except Exception as e:
            print(f"[NFC] Initialization failed: {e}")
    
    def read_card(self, timeout=0.5) -> dict:
        """
        Odczytaj kartę NFC
        
        Args:
            timeout: Timeout w sekundach
            
        Returns:
            dict: {'uid': bytes, 'uid_hex': str, 'type': str} lub None
        """
        if not self.available:
            return None
        
        try:
            uid = self.pn532.read_passive_target(timeout=timeout)
            
            if uid:
                uid_hex = ''.join(['{:02X}'.format(b) for b in uid])
                
                # Sprawdź czy to nowa karta
                if uid_hex != self._last_uid:
                    self._last_uid = uid_hex
                    
                    card_type = "Unknown"
                    if len(uid) == 4:
                        card_type = "MIFARE Classic/Ultralight"
                    elif len(uid) == 7:
                        card_type = "MIFARE DESFire"
                    
                    return {
                        'uid': uid,
                        'uid_hex': uid_hex,
                        'uid_length': len(uid),
                        'type': card_type,
                        'is_new': True
                    }
                else:
                    # Ta sama karta - nadal obecna
                    return {
                        'uid': uid,
                        'uid_hex': uid_hex,
                        'is_new': False
                    }
            else:
                # Brak karty
                if self._last_uid is not None:
                    self._last_uid = None
                return None
                
        except Exception:
            return None
    
    def is_card_present(self) -> bool:
        """Sprawdź czy karta jest obecna"""
        return self._last_uid is not None
```

---

## 🔧 Implementacja Warstwy 2: Services

### `services/storage_manager.py`
```python
"""Storage Manager - JSON persistence"""

import json

class StorageManager:
    """Manager przechowywania danych w JSON"""
    
    def __init__(self, filename='storage.json'):
        """
        Args:
            filename: Nazwa pliku JSON
        """
        self.filename = filename
        self._cache = {}
        self._dirty = False
        self._load()
    
    def _load(self):
        """Wczytaj dane z pliku"""
        try:
            with open(self.filename, 'r') as f:
                self._cache = json.load(f)
            print(f"[Storage] Loaded {len(self._cache)} keys")
        except (OSError, ValueError):
            self._cache = {}
            print("[Storage] File not found, starting fresh")
    
    def save(self):
        """Zapisz dane do pliku (tylko jeśli były zmiany)"""
        if not self._dirty:
            return
        
        try:
            with open(self.filename, 'w') as f:
                json.dump(self._cache, f)
            self._dirty = False
            print(f"[Storage] Saved {len(self._cache)} keys")
        except Exception as e:
            print(f"[Storage] Save failed: {e}")
    
    def set(self, key: str, value):
        """Ustaw wartość"""
        self._cache[key] = value
        self._dirty = True
    
    def get(self, key: str, default=None):
        """Pobierz wartość"""
        return self._cache.get(key, default)
    
    def delete(self, key: str):
        """Usuń klucz"""
        if key in self._cache:
            del self._cache[key]
            self._dirty = True
    
    def clear(self):
        """Wyczyść wszystkie dane"""
        self._cache = {}
        self._dirty = True
    
    def get_all(self) -> dict:
        """Pobierz wszystkie dane"""
        return self._cache.copy()
    
    def has_changes(self) -> bool:
        """Sprawdź czy są niezapisane zmiany"""
        return self._dirty
```

### `services/network_manager.py`
```python
"""Network Manager - WiFi + HTTP"""

import network
import urequests
import ujson
import time

class NetworkManager:
    """Manager sieci WiFi i komunikacji HTTP"""
    
    def __init__(self, server_url: str = None):
        """
        Args:
            server_url: URL serwera (np. "http://192.168.0.16:5000")
        """
        self.wlan = network.WLAN(network.STA_IF)
        self.server_url = server_url
        self._connected = False
        self._ssid = None
        self._ip = None
    
    def connect_wifi(self, ssid: str, password: str, timeout=15) -> bool:
        """
        Połącz z siecią WiFi
        
        Args:
            ssid: Nazwa sieci
            password: Hasło
            timeout: Timeout w sekundach
            
        Returns:
            bool: True jeśli połączono
        """
        print(f"[Network] Connecting to {ssid}...")
        
        self.wlan.active(True)
        
        if self.wlan.isconnected():
            self.wlan.disconnect()
            time.sleep(1)
        
        self.wlan.connect(ssid, password)
        
        start_time = time.time()
        while not self.wlan.isconnected():
            if time.time() - start_time > timeout:
                print("[Network] Connection timeout!")
                return False
            time.sleep(0.5)
        
        self._connected = True
        self._ssid = ssid
        self._ip = self.wlan.ifconfig()[0]
        
        print(f"[Network] Connected! IP: {self._ip}")
        return True
    
    def disconnect_wifi(self):
        """Rozłącz WiFi"""
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self.wlan.active(False)
        self._connected = False
        print("[Network] Disconnected")
    
    def is_connected(self) -> bool:
        """Sprawdź czy WiFi jest połączony"""
        return self._connected and self.wlan.isconnected()
    
    def get_status(self) -> dict:
        """Pobierz status WiFi"""
        return {
            'connected': self.is_connected(),
            'ssid': self._ssid,
            'ip': self._ip,
            'rssi': self.wlan.status('rssi') if self.is_connected() else None
        }
    
    def http_post(self, endpoint: str, data: dict, timeout=10) -> tuple:
        """
        Wyślij żądanie POST
        
        Args:
            endpoint: Ścieżka endpoint (np. "/api/cards")
            data: Dane do wysłania
            timeout: Timeout w sekundach
            
        Returns:
            tuple: (success: bool, response: dict or None)
        """
        if not self.is_connected():
            print("[Network] Not connected!")
            return False, None
        
        if not self.server_url:
            print("[Network] Server URL not set!")
            return False, None
        
        url = self.server_url + endpoint
        headers = {'Content-Type': 'application/json'}
        
        try:
            print(f"[Network] POST {url}")
            response = urequests.post(
                url,
                data=ujson.dumps(data),
                headers=headers,
                timeout=timeout
            )
            
            if 200 <= response.status_code < 300:
                try:
                    response_data = response.json()
                    response.close()
                    return True, response_data
                except:
                    response.close()
                    return True, {}
            else:
                print(f"[Network] HTTP error {response.status_code}")
                response.close()
                return False, None
                
        except Exception as e:
            print(f"[Network] Request failed: {e}")
            return False, None
    
    def http_get(self, endpoint: str, timeout=10) -> tuple:
        """
        Wyślij żądanie GET
        
        Args:
            endpoint: Ścieżka endpoint
            timeout: Timeout w sekundach
            
        Returns:
            tuple: (success: bool, response: dict or None)
        """
        if not self.is_connected():
            return False, None
        
        if not self.server_url:
            return False, None
        
        url = self.server_url + endpoint
        
        try:
            response = urequests.get(url, timeout=timeout)
            
            if 200 <= response.status_code < 300:
                try:
                    response_data = response.json()
                    response.close()
                    return True, response_data
                except:
                    response.close()
                    return True, {}
            else:
                response.close()
                return False, None
                
        except Exception as e:
            print(f"[Network] Request failed: {e}")
            return False, None
```

### `services/auth_manager.py`
```python
"""Authentication Manager"""

class AuthManager:
    """Manager autentykacji (RFID, tokeny)"""
    
    def __init__(self, storage_manager, network_manager):
        """
        Args:
            storage_manager: StorageManager instance
            network_manager: NetworkManager instance
        """
        self.storage = storage_manager
        self.network = network_manager
        self._authenticated = False
        self._rfid_uid = None
        self._access_token = None
        self._refresh_token = None
        
        # Wczytaj zapisane dane
        self._load_auth_data()
    
    def _load_auth_data(self):
        """Wczytaj dane autentykacji z storage"""
        self._rfid_uid = self.storage.get('rfid_uid')
        self._access_token = self.storage.get('access_token')
        self._refresh_token = self.storage.get('refresh_token')
        
        if self._rfid_uid and self._access_token:
            self._authenticated = True
            print(f"[Auth] Loaded saved auth for RFID: {self._rfid_uid}")
    
    def authenticate_rfid(self, rfid_uid: str, chip_secret: str) -> bool:
        """
        Uwierzytelnij kartę RFID
        
        Args:
            rfid_uid: UID karty RFID
            chip_secret: Sekret chipu
            
        Returns:
            bool: True jeśli uwierzytelniono
        """
        print(f"[Auth] Authenticating RFID: {rfid_uid}")
        
        success, response = self.network.http_post('/api/chips/auth-chip', {
            'rfid_uid': rfid_uid,
            'chip_secret': chip_secret
        })
        
        if success and response:
            # Zapisz tokeny
            self._rfid_uid = rfid_uid
            self._access_token = response.get('sb_access_token')
            self._refresh_token = response.get('sb_refresh_token')
            self._authenticated = True
            
            # Zapisz do storage
            self.storage.set('rfid_uid', rfid_uid)
            self.storage.set('access_token', self._access_token)
            self.storage.set('refresh_token', self._refresh_token)
            self.storage.save()
            
            print("[Auth] Authentication successful!")
            return True
        else:
            print("[Auth] Authentication failed!")
            return False
    
    def is_authenticated(self) -> bool:
        """Sprawdź czy jest uwierzytelniony"""
        return self._authenticated
    
    def get_access_token(self) -> str:
        """Pobierz access token"""
        return self._access_token
    
    def get_rfid(self) -> str:
        """Pobierz zapisany RFID UID"""
        return self._rfid_uid
    
    def logout(self):
        """Wyloguj użytkownika"""
        self._authenticated = False
        self._rfid_uid = None
        self._access_token = None
        self._refresh_token = None
        
        self.storage.delete('rfid_uid')
        self.storage.delete('access_token')
        self.storage.delete('refresh_token')
        self.storage.save()
        
        print("[Auth] Logged out")
```

### `services/task_manager.py`
```python
"""Task Manager - Asyncio task coordinator"""

import uasyncio as asyncio

class TaskManager:
    """Manager zadań asynchronicznych"""
    
    def __init__(self):
        self.tasks = []
        self._running = False
    
    def add_task(self, coro, name="unnamed"):
        """
        Dodaj zadanie do listy
        
        Args:
            coro: Coroutine do uruchomienia
            name: Nazwa zadania (dla debugowania)
        """
        task = asyncio.create_task(coro)
        self.tasks.append({'task': task, 'name': name})
        print(f"[TaskManager] Added task: {name}")
    
    async def run_all(self):
        """Uruchom wszystkie zadania równolegle"""
        if not self.tasks:
            print("[TaskManager] No tasks to run")
            return
        
        print(f"[TaskManager] Running {len(self.tasks)} tasks...")
        self._running = True
        
        task_list = [t['task'] for t in self.tasks]
        await asyncio.gather(*task_list)
    
    def stop_all(self):
        """Zatrzymaj wszystkie zadania"""
        print("[TaskManager] Stopping all tasks...")
        for t in self.tasks:
            t['task'].cancel()
        self._running = False
```

---

## 🔧 Implementacja Warstwy 3: UI Engine

### `ui/views.py`
```python
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
```

### `ui/menu_manager.py`
```python
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
```

### `ui/renderer.py`
```python
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
```

---

## 🚀 Main Application - Centralna klasa App

### `main.py`
```python
"""
Main Application - ESP32 
Centralna klasa App z Dependency Injection
"""

import uasyncio as asyncio
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
from ui.views import HomeView, CardReaderView, WiFiView, SettingsView
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
            'current_mode': 'home',  # home, card_reader, wifi, settings
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
            max_val=3,  # 4 menu items
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
            'wifi': WiFiView(),
            'settings': SettingsView()
        }
        
        # Menu Manager
        self.menu = MenuManager(self.renderer)
        self.menu.set_menu_items(['Card Reader', 'WiFi', 'Settings', 'About'])
        
        # Set initial view
        self.renderer.set_view(self.views['home'])
    
    async def nfc_scan_task(self):
        """Task: Skanowanie NFC (async)"""
        print("[Task] NFC scan task started")
        
        while True:
            if self.state['current_mode'] == 'card_reader':
                # Skanuj tylko w trybie card_reader
                card = self.nfc_reader.read_card(timeout=0.3)
                
                if card and card['is_new']:
                    # Nowa karta!
                    self.state['card_present'] = True
                    self.state['card_uid'] = card['uid_hex']
                    self.state['cards_scanned'] += 1
                    
                    self.led.blink(times=1, delay_ms=50)
                    
                    print(f"[NFC] Card detected: {card['uid_hex']}")
                    
                    # Autentykacja (jeśli nie jest uwierzytelniony)
                    if not self.auth.is_authenticated():
                        success = self.auth.authenticate_rfid(
                            card['uid_hex'],
                            self.config.CHIP_SECRET
                        )
                        if success:
                            print("[NFC] Authentication successful!")
                
                elif card and not card['is_new']:
                    # Ta sama karta nadal obecna
                    self.state['card_present'] = True
                else:
                    # Brak karty
                    self.state['card_present'] = False
                    self.state['card_uid'] = None
            
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
                    elif selected == 'WiFi':
                        self.state['current_mode'] = 'wifi'
                        self.renderer.set_view(self.views['wifi'])
                    elif selected == 'Settings':
                        self.state['current_mode'] = 'settings'
                        self.renderer.set_view(self.views['settings'])
                    
                    self.menu.enter_submenu()
                
                elif self.button.was_long_press():
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
```

### `config.py`
```python
"""Application Configuration"""

class Config:
    """Centralna konfiguracja aplikacji"""
    
    # WiFi
    WIFI_SSID = "YourNetworkName"
    WIFI_PASSWORD = "YourPassword"
    AUTO_CONNECT_WIFI = True
    
    # Server
    SERVER_URL = "http://192.168.0.16:5000"
    CHIP_SECRET = "sUUJ7gYG8rkeCrDAr8IV4wMDGfoLbCGUdBtuRhM6X-E"
    
    # Hardware Pins
    LED_PIN = 2
    
    # Encoder
    ENC_CLK = 4
    ENC_DT = 16
    ENC_SW = 17
    
    # OLED Display (I2C)
    OLED_SCL = 22
    OLED_SDA = 21
    
    # NFC Reader (I2C)
    NFC_SCL = 18
    NFC_SDA = 19
    
    # Storage
    STORAGE_FILE = "storage.json"
```

### `boot.py`
```python
"""Boot script"""

import gc
import time

# Garbage collection
gc.collect()

print("\n" + "="*50)
print("  ESP32 MicroPython Boot")
print("="*50)
print("  System ready")
print("="*50 + "\n")

time.sleep(0.5)
```

---

## 📊 Komunikacja Między Warstwami

### Zasada 1: Warstwa nie zna warstwy wyżej
- **Drivers** nie wiedzą o Services ani UI
- **Services** nie wiedzą o UI
- **UI** może używać Drivers i Services

### Zasada 2: Dependency Injection przez App
```python
# ❌ ŹLE - bezpośrednie tworzenie zależności
class MenuManager:
    def __init__(self):
        self.display = Display(22, 21)  # Tight coupling!

# ✅ DOBRZE - przekazanie zależności
class MenuManager:
    def __init__(self, display_driver):
        self.display = display_driver  # Dependency injection
```

### Zasada 3: Shared State przez `app.state`
```python
# NFC Task aktualizuje stan
async def nfc_scan_task(self):
    card = self.nfc_reader.read_card()
    if card:
        self.state['card_present'] = True  # ← Shared state
        self.state['card_uid'] = card['uid_hex']

# Render Task czyta stan
async def render_task(self):
    view_data = {
        'card_present': self.state['card_present'],  # ← Read state
        'card_uid': self.state['card_uid']
    }
    self.renderer.update_data(view_data)
    self.renderer.render()
```

---

## 🔄 Przykładowe Flow

### Scenariusz: Skanowanie karty NFC

```
1. nfc_scan_task() wykrywa kartę
   ↓
2. Aktualizuje app.state['card_present'] = True
   ↓
3. render_task() odczytuje app.state
   ↓
4. Przekazuje dane do renderer.update_data()
   ↓
5. Renderer wywołuje current_view.render(display, data)
   ↓
6. CardReaderView rysuje kartę na OLED
```

### Kod Flow:
```python
# W nfc_scan_task (asyncio task):
async def nfc_scan_task(self):
    while True:
        card = self.nfc_reader.read_card()  # Warstwa 1
        if card:
            self.state['card_uid'] = card['uid_hex']  # Shared state
            
            # Użyj Service Layer
            self.auth.authenticate_rfid(card['uid_hex'], secret)  # Warstwa 2
        
        await asyncio.sleep(0.2)

# W render_task:
async def render_task(self):
    while True:
        # Przygotuj dane z shared state
        data = {'card_uid': self.state['card_uid']}
        
        # Renderuj (Warstwa 3)
        self.renderer.update_data(data)
        self.renderer.render()
        
        await asyncio.sleep_ms(100)
```

---

## 🗺️ Mapowanie Istniejących Plików

### Z obecnej struktury → Nowa struktura

| Obecny plik | Nowa lokalizacja | Warstwa | Uwagi |
|-------------|------------------|---------|-------|
| `main.py` | `main.py` | App | Przerobione na klasę App + asyncio |
| `config.py` | `config.py` | Config | Klasa Config zamiast zmiennych |
| `boot.py` | `boot.py` | Boot | Bez zmian |
| `rotary_irq_esp.py` | `lib/rotary_irq_esp.py` | Lib | Biblioteka |
| `rotary.py` | `lib/rotary.py` | Lib | Biblioteka |
| `ssd1306.py` | `lib/ssd1306.py` | Lib | Biblioteka |
| `pn532.py` | `lib/pn532.py` | Lib | Biblioteka |
| `pn532_i2c.py` | `lib/pn532_i2c.py` | Lib | Biblioteka |
| - | `drivers/encoder.py` | L1 | Nowy wrapper dla rotary |
| - | `drivers/button.py` | L1 | Nowy driver z debouncing |
| - | `drivers/led.py` | L1 | Nowy driver LED |
| `oled_display.py` | `drivers/display_driver.py` | L1 | Uproszczony do czystego drivera |
| `nfc_reader.py` | `drivers/nfc_reader.py` | L1 | Uproszczony do czystego drivera |
| `storage.py` | `services/storage_manager.py` | L2 | Klasa zamiast funkcji |
| `wifi_manager.py` + `http_client.py` | `services/network_manager.py` | L2 | Połączone w jeden service |
| - | `services/auth_manager.py` | L2 | Nowy service dla autentykacji |
| - | `services/task_manager.py` | L2 | Nowy manager zadań asyncio |
| `mode_card_reader.py` | `ui/views.py` (CardReaderView) | L3 | Przekształcone na View |
| `mode_wifi.py` | `ui/views.py` (WiFiView) | L3 | Przekształcone na View |
| - | `ui/menu_manager.py` | L3 | Nowy kontroler menu |
| - | `ui/renderer.py` | L3 | Nowy engine renderowania |

---

## 📝 Kluczowe Różnice od Poprzedniej Wersji

### ❌ **Usunięto:**
- Event Bus / Pub-Sub
- Skomplikowana obsługa zdarzeń
- State Machine z enum
- Nadmiarowe abstrakcje

### ✅ **Dodano:**
- Prostą architekturę 3-warstwową
- Centralny obiekt `App` z Dependency Injection
- Shared state (`app.state`)
- Asyncio tasks z bezpośrednią aktualizacją stanu
- Uproszczone View/Renderer

### 🎯 **Filozofia:**
> "Keep it simple" - Każda warstwa ma jasną odpowiedzialność, komunikacja przez bezpośrednie wywołania i shared state, bez niepotrzebnych abstrakcji.

---

## 🧪 Testowanie

### Test Drivers (Warstwa 1):
```python
# test_drivers/test_encoder.py
def test_encoder_read():
    encoder = Encoder(4, 16, min_val=0, max_val=10)
    value = encoder.read()
    assert 0 <= value <= 10
```

### Test Services (Warstwa 2):
```python
# test_services/test_storage_manager.py
def test_storage_set_get():
    storage = StorageManager('test.json')
    storage.set('key', 'value')
    assert storage.get('key') == 'value'
    storage.save()
```

### Test UI (Warstwa 3):
```python
# test_ui/test_menu_manager.py
def test_menu_navigation():
    menu = MenuManager(None)
    menu.set_menu_items(['Item1', 'Item2', 'Item3'])
    
    menu.navigate_next()
    assert menu.get_selected_index() == 1
    
    menu.navigate_next()
    assert menu.get_selected_index() == 2
```

---

## 🚀 Uruchomienie Projektu

### 1. Flash MicroPython firmware
```bash
esptool.py --chip esp32 --port COM3 erase_flash
esptool.py --chip esp32 --port COM3 write_flash -z 0x1000 esp32-firmware.bin
```

### 2. Upload plików
```bash
# Użyj Pymakr lub mpremote
mpremote connect COM3 fs cp -r . :
```

### 3. Uruchom
```bash
mpremote connect COM3 run main.py
```

---

## 📚 Dokumentacja API

### Drivers API

#### `Encoder`
```python
encoder = Encoder(clk_pin=4, dt_pin=16, min_val=0, max_val=10)
value = encoder.read()              # Odczytaj wartość
changed = encoder.has_changed()     # Sprawdź zmianę
delta = encoder.get_delta()         # Pobierz delta
encoder.set_range(0, 20)           # Zmień zakres
```

#### `Button`
```python
button = Button(pin_num=17)
button.update()                     # Wywołuj co iterację!
if button.is_pressed():            # Sprawdź wciśnięcie
    print("Pressed!")
if button.was_long_press():        # Sprawdź długie wciśnięcie
    print("Long press!")
```

#### `Display`
```python
display = Display(scl_pin=22, sda_pin=21)
display.clear()
display.text("Hello", 0, 0)
display.show()
```

#### `NFCReader`
```python
nfc = NFCReader(scl_pin=18, sda_pin=19)
card = nfc.read_card(timeout=0.5)
if card:
    print(card['uid_hex'])
```

### Services API

#### `StorageManager`
```python
storage = StorageManager('data.json')
storage.set('key', 'value')
value = storage.get('key')
storage.save()
```

#### `NetworkManager`
```python
network = NetworkManager(server_url="http://192.168.0.1:5000")
network.connect_wifi("SSID", "password")
success, data = network.http_post('/api/endpoint', {'key': 'value'})
```

#### `AuthManager`
```python
auth = AuthManager(storage, network)
auth.authenticate_rfid(rfid_uid, chip_secret)
if auth.is_authenticated():
    token = auth.get_access_token()
```

---

## 🎯 Kryteria Sukcesu

✅ **Architektura 3-warstwowa** - Czysta separacja odpowiedzialności  
✅ **Dependency Injection** - App przekazuje zależności  
✅ **Asyncio** - Wszystkie zadania jako async tasks  
✅ **Shared State** - Komunikacja przez `app.state`  
✅ **Prostota** - Brak niepotrzebnych abstrakcji  
✅ **Testowalne** - Każda warstwa testowalna osobno  
✅ **Skalowalne** - Łatwe dodawanie nowych funkcji  

---

## 🏁 Podsumowanie

Ten dokument zawiera kompletne instrukcje do wygenerowania nowego projektu ESP32 z:
- ✅ **3-warstwową architekturą** (Drivers, Services, UI)
- ✅ **Centralnym obiektem App** z Dependency Injection
- ✅ **Asyncio tasks** zamiast Event Bus
- ✅ **Shared state** do komunikacji między taskami
- ✅ **Wszystkimi istniejącymi komponentami** przepisanymi na nową strukturę

**Architektura jest prostsza, bardziej pragmatyczna i łatwiejsza w implementacji niż poprzednia wersja z Event Bus.**

---

## 📖 Dodatkowe Notatki

### Dlaczego bez Event Bus?
- Event Bus dodaje złożoność dla małych projektów
- Shared state + asyncio tasks jest prostsze
- Bezpośrednie wywołania są bardziej czytelne
- Łatwiejsze debugowanie

### Kiedy użyć Event Bus?
- Bardzo duże projekty (>10 modułów)
- Potrzeba loose coupling między wieloma komponentami
- Dynamiczne ładowanie modułów

### Asyncio Best Practices:
- Używaj `await asyncio.sleep()` zamiast `time.sleep()`
- Każdy task powinien mieć `while True` loop
- Używaj `asyncio.sleep_ms()` dla precyzyjnych timeoutów
- Pamiętaj o `try/except` w taskach

---

**Dokument gotowy do użycia przez AI do wygenerowania kompletnego projektu!** 🚀
