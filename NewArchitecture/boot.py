"""Boot script"""

import gc
import time

# Garbage collection
gc.collect()

print("\n" + "="*50)
print("  ESP32 MicroPython Boot")
print("="*50)
print("  System ready")
print("="*50 + "\n")

time.sleep(0.5)
