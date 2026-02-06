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
