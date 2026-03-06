import asyncio
import time
from typing import List, Dict, Any
from app.models import Courier, Order, AssignmentResponse, AssignmentRequest
from app.core.engine import solve_assignment

class GlobalBatcher:
    """
    Simulates an asynchronous background batcher.
    Collects orders over a window of time and then solves them globally.
    """
    def __init__(self, window_seconds: int = 10):
        self.window_seconds = window_seconds
        self.pending_orders: List[Order] = []
        self.pending_couriers: List[Courier] = []
        self.is_running = False
        self._lock = asyncio.Lock()

    async def add_to_batch(self, couriers: List[Courier], orders: List[Order]):
        async with self._lock:
            # We unique-ify by ID
            existing_order_ids = {o.id for o in self.pending_orders}
            for o in orders:
                if o.id not in existing_order_ids:
                    self.pending_orders.append(o)
            
            # For couriers, we usually want the latest state
            self.pending_couriers = couriers # Update with latest courier locations

    async def run_batch_cycle(self):
        """Infinite loop simulating a periodic background worker."""
        while True:
            await asyncio.sleep(self.window_seconds)
            async with self._lock:
                if not self.pending_orders:
                    continue
                
                print(f"[Batcher] Processing {len(self.pending_orders)} orders globally...")
                start_time = time.perf_counter()
                
                # Perform global optimization
                result = solve_assignment(self.pending_couriers, self.pending_orders)
                
                # In a real app, we would push results via WebSockets or save to DB
                # and notify the couriers.
                print(f"[Batcher] Solved {len(result.assignments)} assignments in {result.solved_in_ms}ms")
                
                # Clear batch
                self.pending_orders = []
                
batcher = GlobalBatcher(window_seconds=10)
