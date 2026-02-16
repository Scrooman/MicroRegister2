"""
Sleep Manager
Zarządzanie trybem uśpienia urządzenia
"""

import time
import machine # type: ignore
from machine import Pin # type: ignore


class SleepManager:
    """Zarządzanie trybem uśpienia"""
    
    def __init__(self, wake_button, display, inactivity_timeout=60):
        """
        Inicjalizacja managera uśpienia
        
        Args:
            wake_button: Instancja WakeButton do wybudzania
            display: Instancja Display do wyłączania
            inactivity_timeout: Czas bezczynności do uśpienia (sekundy)
        """
        self.wake_button = wake_button
        self.display = display
        self.inactivity_timeout = inactivity_timeout
        
        # Stan
        self.is_sleeping = False
        self.last_activity_time = time.time()
        self.sleep_enabled = True
        
        print(f"[SleepManager] Initialized - timeout: {inactivity_timeout}s")
    
    def reset_activity_timer(self):
        """Zresetuj timer bezczynności"""
        self.last_activity_time = time.time()
        
        # Jeśli urządzenie było uśpione, obudź je
        if self.is_sleeping:
            self.wake_up()
    
    def set_timeout(self, timeout_seconds):
        """
        Ustaw czas bezczynności do uśpienia
        
        Args:
            timeout_seconds: Czas w sekundach
        """
        self.inactivity_timeout = timeout_seconds
        print(f"[SleepManager] Timeout set to {timeout_seconds}s")
    
    def enable_sleep(self, enabled=True):
        """Włącz/wyłącz automatyczne uśpienie"""
        self.sleep_enabled = enabled
        print(f"[SleepManager] Sleep {'enabled' if enabled else 'disabled'}")
    
    def check_inactivity(self):
        """
        Sprawdź czas bezczynności i uśpij jeśli przekroczony
        
        Returns:
            bool: True jeśli urządzenie zostało uśpione
        """
        if not self.sleep_enabled or self.is_sleeping:
            return False
        
        elapsed = time.time() - self.last_activity_time
        
        if elapsed >= self.inactivity_timeout:
            print(f"[SleepManager] Inactivity timeout ({elapsed:.1f}s) - going to sleep")
            self.go_to_sleep()
            return True
        
        return False
    
    def go_to_sleep(self):
        """Przejdź w tryb uśpienia"""
        if self.is_sleeping:
            return
        
        print("[SleepManager] Going to sleep...")
        
        # Wyłącz ekran
        self.display.power_off()
        
        # Ustaw flagę
        self.is_sleeping = True
        
        print("[SleepManager] Sleeping - press wake button to wake up")
    
    def wake_up(self):
        """Obudź urządzenie"""
        if not self.is_sleeping:
            return
        
        print("[SleepManager] Waking up...")
        
        # Włącz ekran
        self.display.power_on()
        
        # Zresetuj timer
        self.last_activity_time = time.time()
        
        # Wyczyść flagę
        self.is_sleeping = False
        
        print("[SleepManager] Awake")
    
    def check_wake_condition(self):
        """
        Sprawdź czy spełniony jest warunek wybudzenia (wciśnięcie przycisku)
        
        Returns:
            bool: True jeśli należy obudzić urządzenie
        """
        if not self.is_sleeping:
            return False
        
        # Sprawdź przycisk budzący
        if self.wake_button.is_pressed():
            print("[SleepManager] Wake button pressed - waking up")
            self.wake_up()
            return True
        
        return False
    
    def get_inactivity_time(self):
        """
        Pobierz czas bezczynności
        
        Returns:
            float: Czas bezczynności w sekundach
        """
        if self.is_sleeping:
            return self.inactivity_timeout
        
        return time.time() - self.last_activity_time
    
    def get_status(self):
        """
        Pobierz status managera uśpienia
        
        Returns:
            dict: Status
        """
        return {
            'sleeping': self.is_sleeping,
            'enabled': self.sleep_enabled,
            'timeout': self.inactivity_timeout,
            'inactivity': self.get_inactivity_time(),
            'time_to_sleep': max(0, self.inactivity_timeout - self.get_inactivity_time())
        }