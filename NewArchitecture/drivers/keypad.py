"""Keypad Driver - Klawiatura 2x2 matrycowa"""

from machine import Pin # type: ignore
import time 

class Keypad:
    """Driver dla klawiatury 2x2 matrycowej"""
    
    def __init__(self, row_pins: list, col_pins: list, values: list, max_length: int = 4):
        """
        Args:
            row_pins: Lista pinów wierszy [L1, L2]
            col_pins: Lista pinów kolumn [R1, R2]
            values: Lista wartości w formacie [[L1R1, L1R2], [L2R1, L2R2]]
                   np. [['1', '2'], ['3', '4']]
            max_length: Maksymalna długość wprowadzanego ciągu
        """
        self.max_length = max_length
        self.values = values
        self.input_buffer = ""
        
        # Inicjalizacja wierszy jako OUTPUT (będziemy je ustawiać HIGH)
        self.rows = []
        for pin_num in row_pins:
            row = Pin(pin_num, Pin.OUT)
            row.value(0)  # Domyślnie LOW
            self.rows.append(row)
        
        # Inicjalizacja kolumn jako INPUT z PULL_DOWN
        self.cols = []
        for pin_num in col_pins:
            col = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
            self.cols.append(col)
        
        # Debouncing
        self.last_press_time = 0
        self.last_key = None
        self.debounce_ms = 300
    
    def read(self):
        """
        Skanuj matrycę klawiatury
        Returns: Wartość przycisku lub None
        """
        current_time = time.ticks_ms()
        
        # Skanuj każdy wiersz
        for row_idx, row_pin in enumerate(self.rows):
            # Ustaw aktualny wiersz na HIGH
            row_pin.value(1)
            time.sleep_us(10)  # Krótkie opóźnienie na stabilizację
            
            # Sprawdź wszystkie kolumny
            for col_idx, col_pin in enumerate(self.cols):
                if col_pin.value() == 1:
                    # Przycisk wciśnięty!
                    key = self.values[row_idx][col_idx]
                    
                    # Debouncing - sprawdź czy to nowy przycisk lub minął czas
                    if (key != self.last_key or 
                        time.ticks_diff(current_time, self.last_press_time) > self.debounce_ms):
                        self.last_press_time = current_time
                        self.last_key = key
                        
                        # Resetuj wiersz przed zwróceniem
                        row_pin.value(0)
                        return key
            
            # Resetuj wiersz
            row_pin.value(0)
        
        # Jeśli nic nie wciśnięte, resetuj last_key
        self.last_key = None
        return None
    
    def add_to_buffer(self, value):
        """Dodaj wartość do bufora"""
        if len(self.input_buffer) < self.max_length:
            self.input_buffer += str(value)
            return True
        return False
    
    def get_buffer(self):
        """Pobierz zawartość bufora"""
        return self.input_buffer
    
    def clear_buffer(self):
        """Wyczyść bufor"""
        self.input_buffer = ""
    
    def is_buffer_full(self):
        """Sprawdź, czy bufor jest pełny"""
        return len(self.input_buffer) >= self.max_length
    
    def backspace(self):
        """Usuń ostatni znak z bufora"""
        if len(self.input_buffer) > 0:
            self.input_buffer = self.input_buffer[:-1]