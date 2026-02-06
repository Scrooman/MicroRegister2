"""Application Configuration"""

class Config:
    """Centralna konfiguracja aplikacji"""
    
    # WiFi
    WIFI_SSID = "NETIASPOT-a8TRpmR-2.4G"
    WIFI_PASSWORD = "m9zXzVkmbBxTDugkDy"
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
