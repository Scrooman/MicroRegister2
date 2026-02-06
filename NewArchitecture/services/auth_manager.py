"""Authentication Manager"""

class AuthManager:
    """Manager autentykacji (RFID, tokeny)"""
    
    def __init__(self, storage_manager, network_manager):
        """
        Args:
            storage_manager: StorageManager instance
            network_manager: NetworkManager instance
        """
        self.storage = storage_manager
        self.network = network_manager
        self._authenticated = False
        self._rfid_uid = None
        self._access_token = None
        self._refresh_token = None
        
        # Wczytaj zapisane dane
        self._load_auth_data()
    
    def _load_auth_data(self):
        """Wczytaj dane autentykacji z storage"""
        self._rfid_uid = self.storage.get('rfid_uid')
        self._access_token = self.storage.get('access_token')
        self._refresh_token = self.storage.get('refresh_token')
        
        if self._rfid_uid and self._access_token:
            self._authenticated = True
            print(f"[Auth] Loaded saved auth for RFID: {self._rfid_uid}")
    
    def authenticate_rfid(self, rfid_uid: str, chip_secret: str) -> bool:
        """
        Uwierzytelnij kartę RFID
        
        Args:
            rfid_uid: UID karty RFID
            chip_secret: Sekret chipu
            
        Returns:
            bool: True jeśli uwierzytelniono
        """
        print(f"[Auth] Authenticating RFID: {rfid_uid}")
        
        success, response = self.network.http_post('/api/chips/auth-chip', {
            'rfid_uid': rfid_uid,
            'chip_secret': chip_secret
        })
        
        if success and response:
            # Zapisz tokeny
            self._rfid_uid = rfid_uid
            self._access_token = response.get('sb_access_token')
            self._refresh_token = response.get('sb_refresh_token')
            self._authenticated = True
            
            # Zapisz do storage
            self.storage.set('rfid_uid', rfid_uid)
            self.storage.set('access_token', self._access_token)
            self.storage.set('refresh_token', self._refresh_token)
            self.storage.save()
            
            print("[Auth] Authentication successful!")
            return True
        else:
            print("[Auth] Authentication failed!")
            return False
    
    def is_authenticated(self) -> bool:
        """Sprawdź czy jest uwierzytelniony"""
        return self._authenticated
    
    def get_access_token(self) -> str:
        """Pobierz access token"""
        return self._access_token
    
    def get_rfid(self) -> str:
        """Pobierz zapisany RFID UID"""
        return self._rfid_uid
    
    def logout(self):
        """Wyloguj użytkownika"""
        self._authenticated = False
        self._rfid_uid = None
        self._access_token = None
        self._refresh_token = None
        
        self.storage.delete('rfid_uid')
        self.storage.delete('access_token')
        self.storage.delete('refresh_token')
        self.storage.save()
        
        print("[Auth] Logged out")
