"""Network Manager - WiFi + HTTP"""

import network # type: ignore
import urequests # type: ignore
import ujson # type: ignore
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
    
    def connect_wifi(self, ssid: str, password: str, timeout=30) -> bool:
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
    
    def http_post(self, endpoint: str, data: dict, timeout=60, headers=None) -> tuple:
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
            return {'success': False, 'result': None}
        
        if not self.server_url:
            print("[Network] Server URL not set!")
            return {'success': False, 'result': None}
        
        url = self.server_url + endpoint
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        response = None  # DODAJ - inicjalizuj zmienną przed try
        
        try:
            print(f"[Network] POST {url}")
            response = urequests.post(
                url,
                data=ujson.dumps(data),
                headers=headers,
                timeout=timeout
            )
            
            if 200 <= response.status_code < 300:
                    print(f"[Network] POST successful: {response.status_code}")
                    try:
                        response_data = response.json()
                        response.close()
                        
                        return {
                            'success': True, 
                            'result': response_data.get('result', None),
                        }
                    except Exception as e:
                        print(f"[Network] JSON parse error: {e}")
                        response.close()
                        return {'success': True, 'result': {}, 'cookies': {}}
            elif response.status_code != 200:
                try:
                    response_data = response.json()
                    response.close()
                    return {'success': False, 'result': response_data.get('result', None)}
                except:
                    response.close()
                    return {'success': False, 'result': {}}
                
            #jeśli timeout, błąd sieci lub inny problem, złap wyjątek

                
        except Exception as e:
            print(f"[Network] Request failed: {e}")
            
            # POPRAWKA - sprawdź czy response istnieje przed zamknięciem
            if response is not None:
                try:
                    response.close()
                except:
                    pass  # Ignoruj błędy przy zamykaniu
            
            return {'success': False, 'result': None, 'error': str(e)}
        
    
    def http_put(self, endpoint: str, data: dict, timeout=60, headers=None) -> dict:
        """
        Wyślij żądanie PUT
        
        Args:
            endpoint: Ścieżka endpoint (np. "/api/cards")
            data: Dane do wysłania
            timeout: Timeout w sekundach
            headers: Nagłówki HTTP
            
        Returns:
            tuple: (success: bool, response: dict or None)
        """
        if not self.is_connected():
            print("[Network] Not connected!")
            return {'success': False, 'result': None}
        
        if not self.server_url:
            print("[Network] Server URL not set!")
            return {'success': False, 'result': None}
        
        url = self.server_url + endpoint
        if headers is None:
            print("[Network] No headers provided, using default Content-Type: application/json")
            headers = {'Content-Type': 'application/json'}

        response = None  # DODAJ - inicjalizuj zmienną przed try

        try:
            print(f"[Network] PUT {url}")
            response = urequests.put(
                url,
                data=ujson.dumps(data),
                headers=headers,
                timeout=timeout
            )
            if 200 <= response.status_code < 300:
                print(f"[Network] PUT successful: {response.status_code}")
                
                # Sprawdź nagłówki Content-Length i Connection
                content_length = response.headers.get('Content-Length', '0')
                connection = response.headers.get('Connection', '').lower()
                
                print(f"[Network] Content-Length: {content_length}, Connection: {connection}")
                
                # Parsuj tylko jeśli jest zawartość
                if int(content_length) > 0:
                    try:
                        response_data = response.json()
                        response.close()
                        
                        return {
                            'success': True, 
                            'result': response_data.get('result', None),
                        }
                    except Exception as e:
                        print(f"[Network] JSON parse error: {e}")
                        response.close()
                        return {'success': True, 'result': {}}
                else:
                    print("[Network] Empty response body")
                    response.close()
                    return {'success': True, 'result': None}
                    
            elif response.status_code == 401:
                print("[Network] Unauthorized! Access token may be invalid or expired.")
                response.close()
                return {'success': False, 'result': None, "error": 401}
            else:
                print(f"[Network] PUT failed with status code: {response.status_code}")
                response.close()
                return {'success': False, 'result': None, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"[Network] Request failed: {e}")
            
            # POPRAWKA - sprawdź czy response istnieje przed zamknięciem
            if response is not None:
                try:
                    response.close()
                except:
                    pass
            
            return {'success': False, 'result': None, 'error': str(e)}
    
    def http_get(self, endpoint: str, timeout=60) -> dict:
        """
        Wyślij żądanie GET
        
        Args:
            endpoint: Ścieżka endpoint
            timeout: Timeout w sekundach
            
        Returns:
            dict: {'success': bool, 'result': dict or None, 'error': str or None}
        """
        if not self.is_connected():
            return {'success': False, 'result': None, 'error': 'Not connected'}
        
        if not self.server_url:
            return {'success': False, 'result': None, 'error': 'Server URL not set'}
        
        url = self.server_url + endpoint

        response = None  # DODAJ - inicjalizuj zmienną przed try
        
        try:
            response = urequests.get(url, timeout=timeout)
            
            if 200 <= response.status_code < 300:
                try:
                    response_data = response.json()
                    response.close()
                    return {'success': True, 'result': response_data.get('result', None), 'error': None}
                except Exception as e:
                    response.close()
                    return {'success': True, 'result': {}, 'error': str(e)}
            else:
                response.close()
                return {'success': False, 'result': None, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"[Network] Request failed: {e}")
            
            # POPRAWKA - sprawdź czy response istnieje przed zamknięciem
            if response is not None:
                try:
                    response.close()
                except:
                    pass
            
            return {'success': False, 'result': None, 'error': str(e)}