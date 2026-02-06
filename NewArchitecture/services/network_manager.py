"""Network Manager - WiFi + HTTP"""

import network
import urequests
import ujson
import time

class NetworkManager:
    """Manager sieci WiFi i komunikacji HTTP"""
    
    def __init__(self, server_url: str = None):
        """
        Args:
            server_url: URL serwera (np. "http://192.168.0.16:5000")
        """
        self.wlan = network.WLAN(network.STA_IF)
        self.server_url = server_url
        self._connected = False
        self._ssid = None
        self._ip = None
    
    def connect_wifi(self, ssid: str, password: str, timeout=15) -> bool:
        """
        Połącz z siecią WiFi
        
        Args:
            ssid: Nazwa sieci
            password: Hasło
            timeout: Timeout w sekundach
            
        Returns:
            bool: True jeśli połączono
        """
        print(f"[Network] Connecting to {ssid}...")
        
        self.wlan.active(True)
        
        if self.wlan.isconnected():
            self.wlan.disconnect()
            time.sleep(1)
        
        self.wlan.connect(ssid, password)
        
        start_time = time.time()
        while not self.wlan.isconnected():
            if time.time() - start_time > timeout:
                print("[Network] Connection timeout!")
                return False
            time.sleep(0.5)
        
        self._connected = True
        self._ssid = ssid
        self._ip = self.wlan.ifconfig()[0]
        
        print(f"[Network] Connected! IP: {self._ip}")
        return True
    
    def disconnect_wifi(self):
        """Rozłącz WiFi"""
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self.wlan.active(False)
        self._connected = False
        print("[Network] Disconnected")
    
    def is_connected(self) -> bool:
        """Sprawdź czy WiFi jest połączony"""
        return self._connected and self.wlan.isconnected()
    
    def get_status(self) -> dict:
        """Pobierz status WiFi"""
        return {
            'connected': self.is_connected(),
            'ssid': self._ssid,
            'ip': self._ip,
            'rssi': self.wlan.status('rssi') if self.is_connected() else None
        }
    
    def http_post(self, endpoint: str, data: dict, timeout=10) -> tuple:
        """
        Wyślij żądanie POST
        
        Args:
            endpoint: Ścieżka endpoint (np. "/api/cards")
            data: Dane do wysłania
            timeout: Timeout w sekundach
            
        Returns:
            tuple: (success: bool, response: dict or None)
        """
        if not self.is_connected():
            print("[Network] Not connected!")
            return False, None
        
        if not self.server_url:
            print("[Network] Server URL not set!")
            return False, None
        
        url = self.server_url + endpoint
        headers = {'Content-Type': 'application/json'}
        
        try:
            print(f"[Network] POST {url}")
            response = urequests.post(
                url,
                data=ujson.dumps(data),
                headers=headers,
                timeout=timeout
            )
            
            if 200 <= response.status_code < 300:
                try:
                    response_data = response.json()
                    response.close()
                    return True, response_data
                except:
                    response.close()
                    return True, {}
            else:
                print(f"[Network] HTTP error {response.status_code}")
                response.close()
                return False, None
                
        except Exception as e:
            print(f"[Network] Request failed: {e}")
            return False, None
    
    def http_get(self, endpoint: str, timeout=10) -> tuple:
        """
        Wyślij żądanie GET
        
        Args:
            endpoint: Ścieżka endpoint
            timeout: Timeout w sekundach
            
        Returns:
            tuple: (success: bool, response: dict or None)
        """
        if not self.is_connected():
            return False, None
        
        if not self.server_url:
            return False, None
        
        url = self.server_url + endpoint
        
        try:
            response = urequests.get(url, timeout=timeout)
            
            if 200 <= response.status_code < 300:
                try:
                    response_data = response.json()
                    response.close()
                    return True, response_data
                except:
                    response.close()
                    return True, {}
            else:
                response.close()
                return False, None
                
        except Exception as e:
            print(f"[Network] Request failed: {e}")
            return False, None
