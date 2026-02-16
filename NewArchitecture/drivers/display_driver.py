"""OLED Display Driver (SSD1306)"""

from machine import Pin, SoftI2C # type: ignore
import sys
sys.path.append('/lib')

from lib.ssd1306 import SSD1306_I2C

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
        self.oled = SSD1306_I2C(width, height, i2c)
        self.width = width
        self.height = height
        self._powered_on = True  # Dodaj flagę stanu zasilania
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

    def power_off(self):
        """Wyłącz zasilanie ekranu"""
        if not self._powered_on:
            return
        
        try:
            # Wyczyść ekran
            self.clear()
            self.show()
            
            # Wyłącz wyświetlacz (komenda SSD1306)
            self.oled.poweroff()
            self._powered_on = False
            print("[Display] Powered OFF")
        except Exception as e:
            print(f"[Display] Error powering off: {e}")
    
    def power_on(self):
        """Włącz zasilanie ekranu"""
        if self._powered_on:
            return
        
        try:
            # Włącz wyświetlacz
            self.oled.poweron()
            self._powered_on = True
            
            # Odśwież ekran
            self.show()
            print("[Display] Powered ON")
        except Exception as e:
            print(f"[Display] Error powering on: {e}")
    
    def is_powered(self):
        """Sprawdź czy ekran jest włączony"""
        return self._powered_on
