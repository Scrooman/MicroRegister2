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
    
    def _load(self):
        """Wczytaj dane z pliku"""
        try:
            with open(self.filename, 'r') as f:
                self._cache = json.load(f)
            print(f"[Storage] Loaded {len(self._cache)} keys")
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
