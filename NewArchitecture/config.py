"""Application Configuration"""

class Config:
    """Centralna konfiguracja aplikacji"""
    
    # WiFi
    WIFI_SSID = "NETIASPOT-a8TRpmR-2.4G"
    #WIFI_SSID = "Orange_Swiatlowod_7A30"

    WIFI_PASSWORD = "m9zXzVkmbBxTDugkDy"
    #WIFI_PASSWORD = "Salsa_salsa_2022"

    AUTO_CONNECT_WIFI = True
    
    # Server
    SERVER_URL = "https://registry-app-k0b1.onrender.com"
    #SERVER_URL = "http://192.168.0.16:5000"

    #SERVER_URL = "http://192.168.1.70:5000"

    CHIP_SECRET = "sUUJ7gYG8rkeCrDAr8IV4wMDGfoLbCGUdBtuRhM6X-E"
    
    # Hardware Pins - LEDs
    LED_POSITIVE_PIN = 2   # D2 - zielona dioda (pozytywna)
    LED_NEGATIVE_PIN = 13  # D13 - czerwona dioda (negatywna)
    
    
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

    # Keypad (matrycowa 2x2)
    KEYPAD_ROW_PINS = [25, 26]  # L1, L2 (wiersze)
    KEYPAD_COL_PINS = [27, 14]  # R1, R2 (kolumny)
    KEYPAD_VALUES = [
        ['1', '2'],  # Wiersz L1: [L1R1, L1R2]
        ['3', '4']   # Wiersz L2: [L2R1, L2R2]
    ]
    KEYPAD_MAX_LENGTH = 4

    # Wake Button (zastępuje Touch Sensor)
    WAKE_BUTTON_PIN = 12  # D12 (GPIO 12)
    WAKE_BUTTON_PULL_UP = True  # True = przycisk do GND, False = przycisk do VCC
    WAKE_BUTTON_DEBOUNCE_MS = 50  # Czas debouncingu
    
    
    # Sleep Mode
    SLEEP_ENABLED = True
    SLEEP_INACTIVITY_TIMEOUT = 120  # Sekundy bezczynności do uśpienia (domyślnie 60s)
    
