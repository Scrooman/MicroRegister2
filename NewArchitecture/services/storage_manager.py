"""Storage Manager - JSON persistence"""

import json

class StorageManager:
    """Manager przechowywania danych w JSON"""
    
    def __init__(self, filename='storage.json'):
        """
        Args:
            filename: Nazwa pliku JSON
        """

        self.filename = filename
        self._cache = {}
        self._dirty = False
        self._load()

        # jeśli w pamięci nie istnieje klucz chips_auth_data_list, to go inicjalizuj jako pustą listę
        if self.get('chips_auth_data_list') is None:
            print("[Storage] Initializing chips_auth_data_list as empty list")
            # inicjalnie wstaw tablicę: chips_auth_data_list, która będzie przechowywać dane autentykacji kart
            # # tymczasowo testowe dane
            # chips_auth_data_list = [
            #     {
            #         "rfid_uid": "5B96ED06",
            #         "token_data": {
            #             'sb_access_token': "eyJhbGciOiJFUzI1NiIsImtpZCI6IjY2NThmMzU5LWE4N2QtNDFjMy05MTk1LTMzMzQ3MWI3Y2RlMSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2x3cGhhdnZuY2p3Ynp3emV0bGJnLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIzZDMyNjZhYS0xZmM0LTQ3ZWMtYjMzOS0zMWNjOTFmMzMzMzkiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcwNjIwOTQ5LCJpYXQiOjE3NzA2MTczNDksImVtYWlsIjoidGVzdDI1QGV4YW1wbGUuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbCI6InRlc3QyNUBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaG9uZV92ZXJpZmllZCI6ZmFsc2UsInN1YiI6IjNkMzI2NmFhLTFmYzQtNDdlYy1iMzM5LTMxY2M5MWYzMzMzOSJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzcwNjE3MzQ5fV0sInNlc3Npb25faWQiOiI0MDk1N2VmNy1lN2E0LTQ0YjAtYmQ4Mi1jYzExZTdjN2EwMTUiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.I0QIZk5UO3YgSn-2yTq4Yb_O2ySRFqp_Am0EGLa2MX4bvs3dJ0sRjeIC68UqFamzjcP7jdEf_SHqmL6GeoFhSg; sb_refresh_token=4du2w6tvbcz3",
            #             'sb_refresh_token': "7zsf4hxvedll"
            #         }
            #     }
            # ]
            #self.set('chips_auth_data_list', chips_auth_data_list)
            self.set('chips_auth_data_list', [])

            self.save()
        else:
            print(f"[Storage] chips_auth_data_list already exists with {len(self.get('chips_auth_data_list'))} entries")
        # wyświetl aktualne dane po inicjalizacji

        # inicjuj ostatnio autentykowaną kartę RFID
        if self.get('last_authenticated_card') is None:
            print("[Storage] Initializing last_authenticated_card as None")
            # testowa wartość:
            #last_authenticated_card = "5B96ED06"
            #self.set('last_authenticated_card', last_authenticated_card)
            self.set('last_authenticated_card', None)

            self.save()
        else:
            print(f"[Storage] last_authenticated_card already exists: {self.get('last_authenticated_card')}")


        print(f"[Storage] Initial data: {self.get_all()}")
    
    def _load(self):
        """Wczytaj dane z pliku"""
        try:
            with open(self.filename, 'r') as f:
                self._cache = json.load(f)
            print(f"[Storage] Loaded {len(self._cache)} keys")
            print(f"[Storage] Current data: {self._cache}")
        except (OSError, ValueError):
            self._cache = {}
            print("[Storage] File not found, starting fresh")
    
    def save(self):
        """Zapisz dane do pliku (tylko jeśli były zmiany)"""
        if not self._dirty:
            return
        
        try:
            with open(self.filename, 'w') as f:
                json.dump(self._cache, f)
            self._dirty = False
            print(f"[Storage] Saved {len(self._cache)} keys")
        except Exception as e:
            print(f"[Storage] Save failed: {e}")
    
    def set(self, key: str, value):
        """Ustaw wartość"""
        self._cache[key] = value
        self._dirty = True
    
    def get(self, key: str, default=None):
        """Pobierz wartość"""
        return self._cache.get(key, default)
    
    def delete(self, key: str):
        """Usuń klucz"""
        if key in self._cache:
            del self._cache[key]
            self._dirty = True
    
    def clear(self):
        """Wyczyść wszystkie dane"""
        self._cache = {}
        self._dirty = True
    
    def get_all(self) -> dict:
        """Pobierz wszystkie dane"""
        return self._cache.copy()
    
    def has_changes(self) -> bool:
        """Sprawdź czy są niezapisane zmiany"""
        return self._dirty
