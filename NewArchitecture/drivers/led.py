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
