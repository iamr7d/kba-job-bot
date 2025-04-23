import time
from threading import Lock

class GeminiRateLimiter:
    def __init__(self, max_requests_per_minute=15):
        self.max_requests = max_requests_per_minute
        self.timestamps = []
        self.lock = Lock()

    def allow_request(self):
        now = time.time()
        with self.lock:
            # Remove timestamps older than 60 seconds
            self.timestamps = [t for t in self.timestamps if now - t < 60]
            if len(self.timestamps) < self.max_requests:
                self.timestamps.append(now)
                return True
            return False

gemini_rate_limiter = GeminiRateLimiter()
