"""
Wake Button Driver
Prosty przycisk do wybudzania urządzenia
"""

from machine import Pin # type: ignore
import time


class WakeButton:
    """Driver dla przycisku wybudzającego"""
    
    def __init__(self, pin_num, pull_up=True, debounce_ms=50):
        """
        Inicjalizacja przycisku
        
        Args:
            pin_num: Numer pinu GPIO
            pull_up: True = Pull-up (przycisk do GND), False = Pull-down (przycisk do VCC)
            debounce_ms: Czas debouncingu w ms
        """
        self.pin_num = pin_num
        self.debounce_ms = debounce_ms
        self.pull_up = pull_up
        
        # Konfiguracja pinu
        if pull_up:
            self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
            self.active_level = 0  # LOW = wciśnięty
        else:
            self.pin = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
            self.active_level = 1  # HIGH = wciśnięty
        
        # Stan
        self.last_state = not self.active_level
        self.last_change_time = time.ticks_ms()
        self.pressed_count = 0
        
        print(f"[WakeButton] Initialized on pin {pin_num} ({'PULL_UP' if pull_up else 'PULL_DOWN'})")
    
    def is_pressed(self):
        """
        Sprawdź czy przycisk jest wciśnięty (z debouncingiem)
        
        Returns:
            bool: True jeśli wciśnięty
        """
        current_state = self.pin.value()
        current_time = time.ticks_ms()
        
        # Sprawdź debouncing
        if time.ticks_diff(current_time, self.last_change_time) < self.debounce_ms:
            return self.last_state == self.active_level
        
        # Aktualizuj stan
        if current_state != self.last_state:
            self.last_state = current_state
            self.last_change_time = current_time
            
            if current_state == self.active_level:
                self.pressed_count += 1
        
        return current_state == self.active_level
    
    def read_raw(self):
        """Odczytaj surowy stan pinu"""
        return self.pin.value()
    
    def get_press_count(self):
        """Pobierz liczbę wciśnięć"""
        return self.pressed_count
    
    def reset_count(self):
        """Zresetuj licznik wciśnięć"""
        self.pressed_count = 0
    
    def get_status(self):
        """Pobierz status przycisku"""
        return {
            'pin': self.pin_num,
            'pressed': self.is_pressed(),
            'raw_value': self.read_raw(),
            'press_count': self.pressed_count,
            'pull_up': self.pull_up,
            'active_level': self.active_level
        }