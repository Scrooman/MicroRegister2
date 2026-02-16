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
        #self._authenticated = True

        self._rfid_uid = None
        self._access_token = None
        self._refresh_token = None
        
        # Wczytaj zapisane dane
        self._load_auth_data()
    
    def _load_auth_data(self):
        """Wczytaj dane autentykacji z storage"""
        # pobierz ostatnio autentykowaną kartę RFID oraz tokeny z storage
        last_authenticated_card = self.storage.get('last_authenticated_card', None)
        print(f"[Auth] Last authenticated card from storage: {last_authenticated_card}")
        # pobierz tokeny z listy chips_auth_data_list w storage na podstawie last_authenticated_card
        chips_auth_data_list = self.storage.get('chips_auth_data_list', [])
        for chip_auth_data in chips_auth_data_list:
            if chip_auth_data['rfid_uid'] == last_authenticated_card:
                print(f"[Auth] Found matching auth data for RFID: {last_authenticated_card}")
                self._authenticated = True
                self._rfid_uid = chip_auth_data['rfid_uid']
                self._access_token = chip_auth_data['token_data']['sb_access_token']
                self._refresh_token = chip_auth_data['token_data']['sb_refresh_token']
                print(f"[Auth] Loaded access token: {self._access_token}")
                print(f"[Auth] Loaded refresh token: {self._refresh_token}")
            else:
                print(f"[Auth] No matching auth data for RFID: {last_authenticated_card} in this entry: {chip_auth_data['rfid_uid']}")


    def refresh_tokens(self):
        """Odśwież tokeny za pomocą refresh tokena"""
        if not self._refresh_token:
            print("[Auth] No refresh token available!")
            return {'success': False, 'message': "No refresh token available!"}
        
        print("[Auth] Refreshing tokens...")
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'sb_refresh_token={self._refresh_token}'
            #'Cookie': f'sb_access_token=eyJhbGciOiJFUzI1NiIsImtpZCI6IjY2NThmMzU5LWE4N2QtNDFjMy05MTk1LTMzMzQ3MWI3Y2RlMSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2x3cGhhdnZuY2p3Ynp3emV0bGJnLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIzZDMyNjZhYS0xZmM0LTQ3ZWMtYjMzOS0zMWNjOTFmMzMzMzkiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcwNTQwOTE2LCJpYXQiOjE3NzA1MzczMTYsImVtYWlsIjoidGVzdDI1QGV4YW1wbGUuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InRlc3QyNUBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInN1YiI6IjNkMzI2NmFhLTFmYzQtNDdlYy1iMzM5LTMxY2M5MWYzMzMzOSJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcwNTM3MzE2fV0sInNlc3Npb25faWQiOiIxMWM5Y2Q2OS1hN2RlLTRhMDMtYjNjYS1lM2Y2ZThkMTI3ZjIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.povVSAOBM7C7JNkKpB0rK0hIvVZmOGBrKIJ_DJvv2lGb1uwQnbNb9wNe7m0k8vQNdYU37Xs3GatPxL-4xFmqSg;'
        }
        print(f"Headers for refresh request: {headers}")
        refresh_response = self.network.http_post(
            endpoint='/api/auth/esp32/refresh',
            data={}, 
            headers=headers)
        
        if refresh_response['success']:
            print("[Auth] Refresh response: ", refresh_response)
            # Pobierz tokeny z body odpowiedzi
            refresh_result = refresh_response['result']
            self._access_token = refresh_result['sb_access_token']
            self._refresh_token = refresh_result['sb_refresh_token']
            
            # Zapisz nowe tokeny do storage do tablicy chips_auth_data_list
            chips_auth_data_list = self.storage.get('chips_auth_data_list', [])
            for chip_auth_data in chips_auth_data_list:
                if chip_auth_data['rfid_uid'] == self._rfid_uid:
                    chip_auth_data['token_data']['sb_access_token'] = self._access_token
                    chip_auth_data['token_data']['sb_refresh_token'] = self._refresh_token
                    break
            
            self.storage.set('chips_auth_data_list', chips_auth_data_list)
            self.storage.save()  # <-- TO BRAKOWAŁO!
        
            
            print("[Auth] Tokens refreshed successfully!")
            print(f"[Auth] New access token: {self._access_token}")
            return {'success': True, 'message': "Tokens refreshed successfully!"}
        else:
            print("[Auth] Failed to refresh tokens!")
            return {'success': False, 'message': "Failed to refresh tokens!"}
    
    
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
        
        auth_chip_response = self.network.http_post('/api/chips/auth-chip', {
            'rfid_uid': rfid_uid,
            'chip_secret': chip_secret
        })
        print(f"[Auth] Chip auth response: {auth_chip_response}"    )
        if not auth_chip_response['success']:
            print("[Auth] Chip authentication failed!")
            return {"success": False, "message": "Chip authentication failed!"}
        else:
            print("[Auth] Chip authentication successful!")
            auth_chip_result = auth_chip_response['result']
        
        if auth_chip_response['success']:
            # Zapisz tokeny
            chip_auth_data = {
                "rfid_uid": rfid_uid,
                "token_data": {
                    'sb_access_token': auth_chip_result['sb_access_token'],
                    'sb_refresh_token': auth_chip_result['sb_refresh_token']
                }
            }
            # zapisz dane autentykacji do storage w tablicy chips_auth_data_list
            # ostatnio autentykowana karta RFID jest zapisywana w kluczu 'last_authenticated_card' i na jej podstawie można znaleźć odpowiednie tokeny w chips_auth_data_list
            last_authenticated_card = self.storage.get('last_authenticated_card', None)
            if last_authenticated_card != rfid_uid:
                self.storage.set('last_authenticated_card', rfid_uid)
                self.storage.save()
                print(f"[Auth] Updated last_authenticated_card in storage: {rfid_uid}")
            # dodaj nowe dane autentykacji do chips_auth_data_list
            chips_auth_data_list = self.storage.get('chips_auth_data_list', [])
            # wyszukaj czy już istnieje wpis dla tego rfid_uid, jeśli tak to zaktualizuj tokeny, jeśli nie to dodaj nowy wpis
            found = False
            for i, existing_chip_auth_data in enumerate(chips_auth_data_list):
                if existing_chip_auth_data['rfid_uid'] == rfid_uid:
                    chips_auth_data_list[i] = chip_auth_data
                    found = True
                    print(f"[Auth] Updated existing auth data for RFID: {rfid_uid} in chips_auth_data_list")
                    break
            if not found:
                chips_auth_data_list.append(chip_auth_data)
                print(f"[Auth] Added new auth data for RFID: {rfid_uid} to chips_auth_data_list")
            self.storage.set('chips_auth_data_list', chips_auth_data_list)
            self.storage.save()


            # Ustaw dane w managerze
            self._authenticated = True
            self._rfid_uid = rfid_uid
            self._access_token = auth_chip_result['sb_access_token']
            self._refresh_token = auth_chip_result['sb_refresh_token']
            
            print("[Auth] Authentication successful!")
            # odczytaj tokeny z storage
            stored_data = self.storage.get('chips_auth_data_list')
            print(f"[Auth] Stored auth data: {stored_data}")
            return {"success": True, "message": "Authentication successful!"}
        else:
            print("[Auth] Authentication failed!")
            return {"success": False, "message": "Authentication failed!"}
    
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
        self.storage.delete('sb_access_token')
        self.storage.delete('sb_refresh_token')
        self.storage.save()
        
        print("[Auth] Logged out")

    
    def send_chip_detection(self, rfid_uid: str):
        """Wyślij informację o wykryciu karty do serwera"""
        if not self.is_authenticated():
            print("[Auth] Not authenticated, cannot send chip detection!")
            return {"success": False, "message": "Not authenticated!", "error": 401}
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'sb_access_token={self._access_token}'
            #'Cookie': f'sb_access_token=eyJhbGciOiJFUzI1NiIsImtpZCI6IjY2NThmMzU5LWE4N2QtNDFjMy05MTk1LTMzMzQ3MWI3Y2RlMSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2x3cGhhdnZuY2p3Ynp3emV0bGJnLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIzZDMyNjZhYS0xZmM0LTQ3ZWMtYjMzOS0zMWNjOTFmMzMzMzkiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcwNTQwOTE2LCJpYXQiOjE3NzA1MzczMTYsImVtYWlsIjoidGVzdDI1QGV4YW1wbGUuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InRlc3QyNUBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInN1YiI6IjNkMzI2NmFhLTFmYzQtNDdlYy1iMzM5LTMxY2M5MWYzMzMzOSJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcwNTM3MzE2fV0sInNlc3Npb25faWQiOiIxMWM5Y2Q2OS1hN2RlLTRhMDMtYjNjYS1lM2Y2ZThkMTI3ZjIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.povVSAOBM7C7JNkKpB0rK0hIvVZmOGBrKIJ_DJvv2lGb1uwQnbNb9wNe7m0k8vQNdYU37Xs3GatPxL-4xFmqSg;'
        }
        send_chip_detection_response = self.network.http_put(
            endpoint=f'/api/chips/{rfid_uid}/dashboard/tasks', 
            data=None,
            timeout=60,
            headers=headers)

        print(f"[Auth] Chip detection response: {send_chip_detection_response}")
        if not send_chip_detection_response['success'] and send_chip_detection_response.get('error') != 401:
            print("[Auth] Failed to send chip detection!")
            return {"success": False, "message": "Failed to send chip detection!"}
        elif not send_chip_detection_response['success'] and send_chip_detection_response.get('error') == 401:
            print("[Auth] Unauthorized! Access token may be invalid or expired.")
            #wykonaj próbę odświeżenia tokena
            refresh_tokens_response = self.refresh_tokens()
            if not refresh_tokens_response['success']:
                print("[Auth] Failed to refresh tokens after unauthorized error!")
                return {"success": False, "message": "Failed to refresh tokens after unauthorized error!"}
            else:
                print("[Auth] Tokens refreshed successfully, retrying chip detection...")
                headers = {
                    'Content-Type': 'application/json',
                    'Cookie': f'sb_access_token={self._access_token}'
                }
                send_chip_detection_response = self.network.http_put(
                endpoint=f'/api/chips/{rfid_uid}/dashboard/tasks', 
                data=None, 
                timeout=60,
                headers=headers)
                if not send_chip_detection_response['success']:
                    print("[Auth] Failed to send chip detection after refreshing tokens!")
                    return {"success": False, "message": "Failed to send chip detection after refreshing tokens!"}
                else:
                    print("[Auth] Chip detection sent successfully after refreshing tokens!")
                    return {"success": True, "message": "Chip detection sent successfully after refreshing tokens!", "result": send_chip_detection_response['result']}
        else:
            print("[Auth] Chip detection sent successfully!")
            return {"success": True, "message": "Chip detection sent successfully!", "result": send_chip_detection_response['result']}