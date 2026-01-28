import hashlib
import json
import redis.asyncio as redis
from app.core.config import settings

def get_redis_client():
    # Connect to Redis Cache
    client = redis.from_url(settings.redis_url)
    return client

def get_cache_key(tenant_id: str, query_text: str) -> str:
    # 1. Hash the query text
    query_hash = hashlib.sha256(query_text.encode()).hexdigest()

    # 2. Take first 16 characters (enough to be unique)
    short_hash = query_hash[:16]

    # 3. Combine into cache key
    return f"query:{tenant_id}:{short_hash}"

async def get_cached_answer(tenant_id, query_text) -> dict | None:
    # 1. Format Key
    key = get_cache_key(tenant_id, query_text)
    # 2. Connect to Redis Cache
    client = get_redis_client()

    # 3. Obtain Value from Hashed Key
    value = await client.get(key)

    # 4. If there is a value, return the value
    if value:
        return json.loads(value)
    return None

async def cache_answer(tenant_id, query_text, answer: dict, ttl=3600):
    # 1. Format Key
    key = get_cache_key(tenant_id, query_text)
    # 2. Connect to Redis Cache
    client = get_redis_client()

    # 3. Set the value to the key in cache
    await client.set(key, json.dumps(answer), ex=ttl)