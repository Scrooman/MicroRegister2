"""NFC Reader Driver (PN532)"""

from machine import I2C, Pin # type: ignore
import sys
sys.path.append('/lib')

from lib.pn532_i2c import PN532_I2C

class NFCReader:
    """Sterownik czytnika NFC PN532"""
    
    def __init__(self, scl_pin: int, sda_pin: int, i2c_id=1):
        """
        Args:
            scl_pin: Pin SCL dla I2C
            sda_pin: Pin SDA dla I2C
            i2c_id: ID magistrali I2C
        """
        self.available = False
        self._last_uid = None
        
        try:
            i2c = I2C(i2c_id, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000)
            self.pn532 = PN532_I2C(i2c, debug=False)
            
            # Sprawdź firmware
            ic, ver, rev, support = self.pn532.firmware_version
            print(f"[NFC] PN532 v{ver}.{rev} detected")
            
            # Konfiguruj czytnik
            self.pn532.SAM_configuration()
            self.available = True
            
        except Exception as e:
            print(f"[NFC] Initialization failed: {e}")
    
    def read_card(self, timeout=0.5) -> dict:
        """
        Odczytaj kartę NFC
        
        Args:
            timeout: Timeout w sekundach
            
        Returns:
            dict: {'uid': bytes, 'uid_hex': str, 'type': str, 'is_new': bool} lub None
        """
        if not self.available:
            return None
        
        try:
            uid = self.pn532.read_passive_target(timeout=timeout)
            
            if uid:
                uid_hex = ''.join(['{:02X}'.format(b) for b in uid])
                
                # Sprawdź czy to nowa karta
                if uid_hex != self._last_uid:
                    self._last_uid = uid_hex
                    
                    card_type = "Unknown"
                    if len(uid) == 4:
                        card_type = "MIFARE Classic/Ultralight"
                    elif len(uid) == 7:
                        card_type = "MIFARE DESFire"
                    
                    return {
                        'uid': uid,
                        'uid_hex': uid_hex,
                        'uid_length': len(uid),
                        'type': card_type,
                        'is_new': True
                    }
                else:
                    # Ta sama karta - nadal obecna
                    return {
                        'uid': uid,
                        'uid_hex': uid_hex,
                        'is_new': False
                    }
            else:
                # Brak karty
                if self._last_uid is not None:
                    self._last_uid = None
                return None
                
        except Exception:
            return None
    
    def is_card_present(self) -> bool:
        """Sprawdź czy karta jest obecna"""
        return self._last_uid is not None
