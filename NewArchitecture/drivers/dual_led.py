"""
Dual LED Driver
Obsługa dwóch diod LED (pozytywna/negatywna) z predefiniowanymi trybami
"""

from machine import Pin # type: ignore
import time
import asyncio # type: ignore


class DualLED:
    """Driver dla dwóch diod LED z predefiniowanymi wzorcami"""
    
    # Predefiniowane tryby
    MODES = {
        # Tryby pozytywne (zielona dioda)
        'positive_confirmation': {
            'led': 'positive',
            'pattern': 'solid',
            'duration': 3000,  # 3 sekundy
        },
        'positive_indicator': {
            'led': 'positive',
            'pattern': 'blink',
            'times': 3,
            'on_time': 200,
            'off_time': 200,
        },
        'positive_quick': {
            'led': 'positive',
            'pattern': 'blink',
            'times': 1,
            'on_time': 100,
            'off_time': 0,
        },
        'positive_pulse': {
            'led': 'positive',
            'pattern': 'blink',
            'times': 2,
            'on_time': 100,
            'off_time': 100,
        },
        
        # Tryby negatywne (czerwona dioda)
        'negative_confirmation': {
            'led': 'negative',
            'pattern': 'solid',
            'duration': 3000,  # 3 sekundy
        },
        'negative_indicator': {
            'led': 'negative',
            'pattern': 'blink',
            'times': 3,
            'on_time': 200,
            'off_time': 200,
        },
        'negative_quick': {
            'led': 'negative',
            'pattern': 'blink',
            'times': 1,
            'on_time': 100,
            'off_time': 0,
        },
        'negative_error': {
            'led': 'negative',
            'pattern': 'blink',
            'times': 5,
            'on_time': 150,
            'off_time': 150,
        },
        'negative_warning': {
            'led': 'negative',
            'pattern': 'blink',
            'times': 2,
            'on_time': 500,
            'off_time': 300,
        },
        
        # Tryby specjalne (obie diody)
        'alternating': {
            'led': 'both',
            'pattern': 'alternate',
            'times': 3,
            'on_time': 300,
        },
        'attention': {
            'led': 'both',
            'pattern': 'alternate',
            'times': 5,
            'on_time': 200,
        },
    }
    
    def __init__(self, positive_pin, negative_pin):
        """
        Inicjalizacja dwóch diod LED
        
        Args:
            positive_pin: Pin dla diody pozytywnej (zielonej)
            negative_pin: Pin dla diody negatywnej (czerwonej)
        """
        self.positive_pin = positive_pin
        self.negative_pin = negative_pin
        
        # Konfiguracja pinów
        self.positive = Pin(positive_pin, Pin.OUT)
        self.negative = Pin(negative_pin, Pin.OUT)
        
        # Wyłącz obie diody na start
        self.positive.off()
        self.negative.off()
        
        # Stan
        self._positive_state = False
        self._negative_state = False
        self._current_task = None
        
        print(f"[DualLED] Initialized - Positive: {positive_pin}, Negative: {negative_pin}")
    
    def positive_on(self):
        """Włącz diodę pozytywną (zieloną)"""
        self.positive.on()
        self._positive_state = True
    
    def positive_off(self):
        """Wyłącz diodę pozytywną (zieloną)"""
        self.positive.off()
        self._positive_state = False
    
    def negative_on(self):
        """Włącz diodę negatywną (czerwoną)"""
        self.negative.on()
        self._negative_state = True
    
    def negative_off(self):
        """Wyłącz diodę negatywną (czerwoną)"""
        self.negative.off()
        self._negative_state = False
    
    def all_off(self):
        """Wyłącz obie diody"""
        self.positive_off()
        self.negative_off()
    
    def all_on(self):
        """Włącz obie diody"""
        self.positive_on()
        self.negative_on()
    
    def blink_positive(self, times=1, on_time=100, off_time=100):
        """
        Mrugnij diodą pozytywną
        
        Args:
            times: Liczba mrugnięć
            on_time: Czas świecenia (ms)
            off_time: Czas wygaszenia (ms)
        """
        for _ in range(times):
            self.positive_on()
            time.sleep_ms(on_time)
            self.positive_off()
            if off_time > 0:
                time.sleep_ms(off_time)
    
    def blink_negative(self, times=1, on_time=100, off_time=100):
        """
        Mrugnij diodą negatywną
        
        Args:
            times: Liczba mrugnięć
            on_time: Czas świecenia (ms)
            off_time: Czas wygaszenia (ms)
        """
        for _ in range(times):
            self.negative_on()
            time.sleep_ms(on_time)
            self.negative_off()
            if off_time > 0:
                time.sleep_ms(off_time)
    
    def blink_alternate(self, times=3, on_time=200):
        """
        Mrugnij na przemian obiema diodami
        
        Args:
            times: Liczba cykli
            on_time: Czas świecenia każdej diody (ms)
        """
        for _ in range(times):
            self.positive_on()
            self.negative_off()
            time.sleep_ms(on_time)
            
            self.positive_off()
            self.negative_on()
            time.sleep_ms(on_time)
        
        self.all_off()
    
    def show_mode(self, mode_name):
        """
        Uruchom predefiniowany tryb LED
        
        Args:
            mode_name: Nazwa trybu (np. 'positive_confirmation')
        """
        if mode_name not in self.MODES:
            print(f"[DualLED] Unknown mode: {mode_name}")
            return
        
        mode = self.MODES[mode_name]
        led_type = mode['led']
        pattern = mode['pattern']
        
        # Wyłącz obie diody przed rozpoczęciem
        self.all_off()
        
        if pattern == 'solid':
            # Świecenie ciągłe przez określony czas
            duration = mode.get('duration', 1000)
            
            if led_type == 'positive':
                self.positive_on()
            elif led_type == 'negative':
                self.negative_on()
            elif led_type == 'both':
                self.all_on()
            
            time.sleep_ms(duration)
            self.all_off()
            
        elif pattern == 'blink':
            # Mruganie
            times = mode.get('times', 1)
            on_time = mode.get('on_time', 100)
            off_time = mode.get('off_time', 100)
            
            if led_type == 'positive':
                self.blink_positive(times, on_time, off_time)
            elif led_type == 'negative':
                self.blink_negative(times, on_time, off_time)
            elif led_type == 'both':
                # Obie jednocześnie
                for _ in range(times):
                    self.all_on()
                    time.sleep_ms(on_time)
                    self.all_off()
                    if off_time > 0:
                        time.sleep_ms(off_time)
        
        elif pattern == 'alternate':
            # Na przemian
            times = mode.get('times', 3)
            on_time = mode.get('on_time', 200)
            self.blink_alternate(times, on_time)
    
    async def show_mode_async(self, mode_name):
        """
        Uruchom predefiniowany tryb LED (async - nie blokuje)
        
        Args:
            mode_name: Nazwa trybu
        """
        if mode_name not in self.MODES:
            print(f"[DualLED] Unknown mode: {mode_name}")
            return
        
        mode = self.MODES[mode_name]
        led_type = mode['led']
        pattern = mode['pattern']
        
        # Wyłącz obie diody przed rozpoczęciem
        self.all_off()
        
        if pattern == 'solid':
            duration = mode.get('duration', 1000)
            
            if led_type == 'positive':
                self.positive_on()
            elif led_type == 'negative':
                self.negative_on()
            elif led_type == 'both':
                self.all_on()
            
            await asyncio.sleep_ms(duration)
            self.all_off()
            
        elif pattern == 'blink':
            times = mode.get('times', 1)
            on_time = mode.get('on_time', 100)
            off_time = mode.get('off_time', 100)
            
            for _ in range(times):
                if led_type == 'positive':
                    self.positive_on()
                elif led_type == 'negative':
                    self.negative_on()
                elif led_type == 'both':
                    self.all_on()
                
                await asyncio.sleep_ms(on_time)
                self.all_off()
                
                if off_time > 0:
                    await asyncio.sleep_ms(off_time)
        
        elif pattern == 'alternate':
            times = mode.get('times', 3)
            on_time = mode.get('on_time', 200)
            
            for _ in range(times):
                self.positive_on()
                self.negative_off()
                await asyncio.sleep_ms(on_time)
                
                self.positive_off()
                self.negative_on()
                await asyncio.sleep_ms(on_time)
            
            self.all_off()
    
    def get_state(self):
        """Pobierz stan diod"""
        return {
            'positive': self._positive_state,
            'negative': self._negative_state
        }
    
    def get_available_modes(self):
        """Pobierz listę dostępnych trybów"""
        return list(self.MODES.keys())