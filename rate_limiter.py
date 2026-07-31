import asyncio
import time

class AsyncRateLimiter:
    def __init__(self, rate: float = 25):
        self.rate = rate
        self.tokens = rate
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.updated_at
            self.tokens += elapsed * self.rate
            if self.tokens > self.rate:
                self.tokens = self.rate
            self.updated_at = now
            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1