import redis
from backend.core.config import settings

def check_redis() -> bool:
    try: return bool(redis.from_url(settings.redis_url).ping())
    except redis.RedisError: return False
