import json
import redis.asyncio as redis
import numpy as np
from typing import Optional, List, Dict, Any
from core.config import settings

# Redis connection pool
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2",
            encoding="utf8",
            decode_responses=True
        )
    return _redis_client


async def set_cached_docs(docs: List[Dict[str, str]], ttl: int = 3600) -> bool:
    try:
        redis_client = await get_redis_client()
        docs_json = json.dumps(docs)
        await redis_client.setex("policies:docs", ttl, docs_json)
        return True
    except Exception as e:
        print(f"Error caching docs: {str(e)}")
        return False


async def get_cached_docs() -> Optional[List[Dict[str, str]]]:
    try:
        redis_client = await get_redis_client()
        docs_json = await redis_client.get("policies:docs")
        if docs_json:
            return json.loads(docs_json)
        return None
    except Exception as e:
        print(f"Error retrieving cached docs: {str(e)}")
        return None


async def set_cached_embeddings(embeddings: np.ndarray, ttl: int = 3600) -> bool:
    try:
        redis_client = await get_redis_client()
        embeddings_list = embeddings.tolist()  # Convert numpy array to list for JSON serialization
        embeddings_json = json.dumps(embeddings_list)
        await redis_client.setex("policies:embeddings", ttl, embeddings_json)
        return True
    except Exception as e:
        print(f"Error caching embeddings: {str(e)}")
        return False


async def get_cached_embeddings() -> Optional[np.ndarray]:
    try:
        redis_client = await get_redis_client()
        embeddings_json = await redis_client.get("policies:embeddings")
        if embeddings_json:
            embeddings_list = json.loads(embeddings_json)
            return np.array(embeddings_list)
        return None
    except Exception as e:
        print(f"Error retrieving cached embeddings: {str(e)}")
        return None


async def invalidate_policies_cache() -> bool:
    try:
        redis_client = await get_redis_client()
        await redis_client.delete("policies:docs", "policies:embeddings")
        return True
    except Exception as e:
        print(f"Error invalidating cache: {str(e)}")
        return False


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
