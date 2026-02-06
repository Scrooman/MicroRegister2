"""Task Manager - Asyncio task coordinator"""

import uasyncio as asyncio

class TaskManager:
    """Manager zadań asynchronicznych"""
    
    def __init__(self):
        self.tasks = []
        self._running = False
    
    def add_task(self, coro, name="unnamed"):
        """
        Dodaj zadanie do listy
        
        Args:
            coro: Coroutine do uruchomienia
            name: Nazwa zadania (dla debugowania)
        """
        task = asyncio.create_task(coro)
        self.tasks.append({'task': task, 'name': name})
        print(f"[TaskManager] Added task: {name}")
    
    async def run_all(self):
        """Uruchom wszystkie zadania równolegle"""
        if not self.tasks:
            print("[TaskManager] No tasks to run")
            return
        
        print(f"[TaskManager] Running {len(self.tasks)} tasks...")
        self._running = True
        
        task_list = [t['task'] for t in self.tasks]
        await asyncio.gather(*task_list)
    
    def stop_all(self):
        """Zatrzymaj wszystkie zadania"""
        print("[TaskManager] Stopping all tasks...")
        for t in self.tasks:
            t['task'].cancel()
        self._running = False
