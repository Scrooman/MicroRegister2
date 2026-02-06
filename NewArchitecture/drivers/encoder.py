"""Rotary Encoder Driver"""

import sys
sys.path.append('/lib')

from lib.rotary_irq_esp import RotaryIRQ

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
